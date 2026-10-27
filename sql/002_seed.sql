-- DML: the made-up accounts and 12,400 synthetic notes (a size where a restore takes a measurable moment).
-- Accounts are seeded with the hash '!', which can never match a password; `make run` gives them throwaway passwords in memory.
-- Nothing here is real personal data. Run again safely: it inserts only when the tables are empty.

INSERT INTO users (username, role, password_hash) VALUES
    ('ada', 'admin', '!'),
    ('bruno', 'member', '!'),
    ('chen', 'member', '!'),
    ('dana', 'readonly', '!')
ON CONFLICT (username) DO NOTHING;

INSERT INTO notes (owner_id, title, body, created_at, updated_at)
SELECT
    (SELECT id FROM users WHERE username = CASE WHEN g % 2 = 0 THEN 'bruno' ELSE 'chen' END),
    'Synthetic note ' || g,
    'Synthetic body for the restore test, row ' || g || '. No personal data.',
    TIMESTAMPTZ '2026-09-01 00:00:00+00' + g * interval '3 minutes',
    TIMESTAMPTZ '2026-09-01 00:00:00+00' + g * interval '3 minutes'
FROM generate_series(1, 12400) AS g
WHERE NOT EXISTS (SELECT 1 FROM notes);
