import os
import shutil
import stat
import subprocess
import tempfile
from pathlib import Path

from django.conf import settings
from django.contrib.auth.models import User as DjangoUser
from django.contrib.sessions.models import Session
from django.test import SimpleTestCase

from scorebrowser.models import ChartPair, User


REPO_ROOT = settings.BASE_DIR.parent
CLONE_SCRIPT = REPO_ROOT / 'scripts' / 'clone_prod_to_staging.ps1'
SANITIZE_SQL = REPO_ROOT / 'scripts' / 'sanitize_staging.sql'
ENV_EXAMPLE = REPO_ROOT / '.env.staging-clone.example'
GITIGNORE = REPO_ROOT / '.gitignore'


def _find_powershell():
    return shutil.which('pwsh') or shutil.which('powershell')


def _env_with_dummy_mysql_tools(tmp):
    tool_dir = tmp / 'bin'
    tool_dir.mkdir()
    for tool in ('mysqldump', 'mysql', 'mysqldump.exe', 'mysql.exe'):
        stub = tool_dir / tool
        stub.write_text('#!/bin/sh\nexit 0\n', encoding='utf-8')
        stub.chmod(stub.stat().st_mode | stat.S_IXUSR)
    env = dict(os.environ)
    env['PATH'] = f"{tool_dir}{os.pathsep}{env.get('PATH', '')}"
    return env


class StagingCloneArtifactsTests(SimpleTestCase):
    def test_required_files_exist_with_lf_line_endings(self):
        for path in (CLONE_SCRIPT, SANITIZE_SQL, ENV_EXAMPLE):
            self.assertTrue(path.exists(), f'Missing artifact: {path}')
            raw = path.read_bytes()
            self.assertNotIn(b'\r', raw, f'CRLF found in {path}')

    def test_gitignore_excludes_local_staging_clone_env(self):
        lines = [line.strip() for line in GITIGNORE.read_text(encoding='utf-8').splitlines()]
        self.assertIn('.env.staging-clone', lines)

    def test_env_example_documents_required_keys(self):
        text = ENV_EXAMPLE.read_text(encoding='utf-8')
        for key in (
            'DB_HOST=',
            'DB_PORT=',
            'DB_CA_CERT_PATH=',
            'PPRX_DUMP_USER=',
            'PPRX_STAGING_USER=',
        ):
            self.assertIn(key, text)

    def test_sanitize_sql_matches_django_tables_and_columns(self):
        sql = SANITIZE_SQL.read_text(encoding='utf-8')

        self.assertIn("DATABASE() != 'pprx_staging'", sql)
        self.assertIn("SIGNAL SQLSTATE '45000'", sql)

        self.assertIn(DjangoUser._meta.db_table, sql)
        self.assertIn(User._meta.db_table, sql)
        self.assertIn(Session._meta.db_table, sql)
        self.assertIn(User._meta.get_field('django_user').column, sql)

        for field_name in (
            'access_token',
            'refresh_token',
            'reauth',
            'webhooked',
            'pulling_scores',
        ):
            self.assertIn(User._meta.get_field(field_name).column, sql)

        self.assertIn("is_staff = 0", sql)
        self.assertIn("username != 'rrwoods'", sql)
        self.assertIn("INFORMATION_SCHEMA.COLUMNS", sql)
        self.assertIn("synchronization_started_at", sql)
        self.assertIn("TRUNCATE TABLE django_session;", sql)

    def test_clone_script_syntax_and_dry_run(self):
        ps = _find_powershell()
        if ps is None:
            self.skipTest('Neither pwsh nor powershell is available')

        with tempfile.TemporaryDirectory() as temp_dir:
            tmp = Path(temp_dir)
            ca_path = tmp / 'ca-cert.crt'
            ca_path.write_text('-----BEGIN CERTIFICATE-----\nDUMMY\n-----END CERTIFICATE-----\n', encoding='utf-8')

            env_file = tmp / '.env.staging-clone'
            env_file.write_text(
                f'DB_HOST=db.example.com\n'
                f'DB_PORT=25060\n'
                f'DB_CA_CERT_PATH="{ca_path}"\n'
                f'PPRX_DUMP_USER=pprx_dump\n'
                f'PPRX_STAGING_USER=pprx_staging\n',
                encoding='utf-8',
            )

            env = _env_with_dummy_mysql_tools(tmp)

            syntax_cmd = [
                ps,
                '-NoProfile',
                '-Command',
                f"$errors = $null; [void][System.Management.Automation.Language.Parser]::ParseFile('{CLONE_SCRIPT}', [ref]$null, [ref]$errors); if ($errors) {{ $errors | Out-String | Write-Error; exit 1 }}",
            ]
            syntax_proc = subprocess.run(syntax_cmd, capture_output=True, text=True, timeout=15)
            self.assertEqual(syntax_proc.returncode, 0, syntax_proc.stderr or syntax_proc.stdout)

            dry_run_cmd = [
                ps,
                '-NoProfile',
                '-ExecutionPolicy',
                'Bypass',
                '-File',
                str(CLONE_SCRIPT),
                '-EnvFile',
                str(env_file),
                '-DryRun',
            ]
            proc = subprocess.run(dry_run_cmd, capture_output=True, text=True, timeout=15, env=env)
            self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout)

            out = proc.stdout
            chart_pairs_table = ChartPair._meta.db_table
            self.assertIn('--ssl-mode=VERIFY_CA', out)
            self.assertIn('--single-transaction', out)
            self.assertIn('--set-gtid-purged=OFF', out)
            self.assertIn('--no-tablespaces', out)
            self.assertIn('--default-character-set=utf8mb4', out)
            self.assertIn('--quick', out)
            self.assertIn('--compress', out)
            self.assertIn(f'--ignore-table=ebdb.{chart_pairs_table} ', out)
            self.assertIn(f'--no-data --result-file=', out)
            self.assertIn(f' ebdb {chart_pairs_table}', out)
            self.assertNotIn('--databases', out)
            self.assertIn('pprx_staging', out)
            self.assertIn('sanitize_staging.sql', out)

    def test_clone_script_errors_when_env_file_or_ca_cert_missing(self):
        ps = _find_powershell()
        if ps is None:
            self.skipTest('Neither pwsh nor powershell is available')

        with tempfile.TemporaryDirectory() as temp_dir:
            tmp = Path(temp_dir)
            env = _env_with_dummy_mysql_tools(tmp)

            missing_env = tmp / 'does-not-exist.env'
            proc = subprocess.run(
                [ps, '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', str(CLONE_SCRIPT), '-EnvFile', str(missing_env), '-DryRun'],
                capture_output=True,
                text=True,
                timeout=15,
                env=env,
            )
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn('Config file not found', proc.stderr + proc.stdout)

            bad_ca_env = tmp / '.env.bad-ca'
            bad_ca_env.write_text(
                'DB_HOST=db.example.com\n'
                'DB_PORT=25060\n'
                f'DB_CA_CERT_PATH={tmp / "missing-ca.crt"}\n'
                'PPRX_DUMP_USER=pprx_dump\n'
                'PPRX_STAGING_USER=pprx_staging\n',
                encoding='utf-8',
            )
            proc = subprocess.run(
                [ps, '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', str(CLONE_SCRIPT), '-EnvFile', str(bad_ca_env), '-DryRun'],
                capture_output=True,
                text=True,
                timeout=15,
                env=env,
            )
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn('CA certificate file not found', proc.stderr + proc.stdout)
