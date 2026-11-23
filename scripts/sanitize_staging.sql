-- Sanitize pprx_staging immediately after restoring a prod dump.
-- Aborts via SIGNAL SQLSTATE '45000' if executed against any database other than pprx_staging.

DROP PROCEDURE IF EXISTS _pprx_sanitize_staging;

DELIMITER $$
CREATE PROCEDURE _pprx_sanitize_staging()
SQL SECURITY INVOKER
BEGIN
    DECLARE v_has_sync_started_at INT DEFAULT 0;

    IF DATABASE() IS NULL OR DATABASE() != 'pprx_staging' THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Refusing to run sanitize_staging.sql: active database must be pprx_staging';
    END IF;

    UPDATE auth_user
    SET email = '',
        password = '!unusable',
        is_superuser = 0
    WHERE is_staff = 0
      AND username != 'rrwoods';

    UPDATE scorebrowser_user AS su
    LEFT JOIN auth_user AS au ON au.id = su.django_user_id
    SET su.access_token = NULL,
        su.refresh_token = NULL,
        su.reauth = 0
    WHERE au.username IS NULL
       OR au.username != 'rrwoods';

    UPDATE scorebrowser_user
    SET webhooked = 0,
        pulling_scores = 0;

    SELECT COUNT(*)
    INTO v_has_sync_started_at
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'scorebrowser_user'
      AND COLUMN_NAME = 'synchronization_started_at';

    IF v_has_sync_started_at > 0 THEN
        PREPARE sync_stmt FROM 'UPDATE scorebrowser_user SET synchronization_started_at = NULL';
        EXECUTE sync_stmt;
        DEALLOCATE PREPARE sync_stmt;
    END IF;

    TRUNCATE TABLE django_session;
END$$
DELIMITER ;

CALL _pprx_sanitize_staging();
DROP PROCEDURE IF EXISTS _pprx_sanitize_staging;
