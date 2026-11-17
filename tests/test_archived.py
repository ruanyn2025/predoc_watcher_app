import sqlite3
import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app
import db
import i18n


class ArchivedTest(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(':memory:')
        self.conn.row_factory = sqlite3.Row
        db.init(self.conn)
        self.key = db.add_manual_job(self.conn, {'title': 'Archive example'})
        db.mark_applied(self.conn, self.key)
        self.today = date.today().isoformat()
        db.add_annotation(self.conn, self.key, 'event', label='Interview', on_date=self.today)

    def tearDown(self):
        self.conn.close()

    def test_archive_restore_preserves_data(self):
        original = db.applications(self.conn)[0]
        annotations = db.annotations_for(self.conn, [self.key])
        self.assertTrue(app.api_stage(self.conn, {'key': self.key, 'stage': 'closed'})['ok'])
        self.assertEqual(db.applications(self.conn), [])
        self.assertEqual(db.applications(self.conn, archived=True)[0]['key'], self.key)
        self.assertEqual(db.stats(self.conn)['applications'], 0)
        self.assertEqual(db.stats(self.conn)['archived'], 1)
        self.assertEqual(db.starred_jobs(self.conn), [])
        db.set_stage(self.conn, self.key, 'applied')
        self.assertEqual(db.applications(self.conn, archived=True), [])
        self.assertEqual(db.applications(self.conn)[0]['applied_at'], original['applied_at'])
        self.assertEqual(db.annotations_for(self.conn, [self.key]), annotations)
        self.assertEqual(db.stats(self.conn)['applications'], 1)
        self.assertEqual(db.stats(self.conn)['archived'], 0)

    def test_existing_closed_pages_and_calendar(self):
        db.set_stage(self.conn, self.key, 'closed')
        for lang in i18n.LANGS:
            db.set_meta(self.conn, 'lang', lang)
            active = app.page_applications(self.conn, {}).decode()
            archived = app.page_archived(self.conn, {}).decode()
            self.assertNotIn('id="job-' + self.key + '"', active)
            self.assertIn('id="job-' + self.key + '"', archived)
            self.assertNotIn('>archived.restore_hint<', archived)
        calendar = app.page_calendar(self.conn, {'ym': [self.today[:7]]}).decode()
        self.assertIn('/archived#job-' + self.key, calendar)
        self.assertNotIn('/applications#job-' + self.key, calendar)
        db.unmark_applied(self.conn, self.key)
        self.assertEqual(db.applications(self.conn, archived=True), [])
        self.assertEqual(len(db.starred_jobs(self.conn)), 1)
        self.assertIn('/starred#job-' + self.key, app.page_calendar(self.conn, {}).decode())

    def test_missing_stage_stays_active(self):
        for stage in (None, '', 'test', 'interview'):
            self.conn.execute('UPDATE stars SET stage=? WHERE key=?', (stage, self.key))
            self.assertEqual(len(db.applications(self.conn)), 1)
            self.assertEqual(db.applications(self.conn)[0]['stage'], 'applied')
            self.assertEqual(db.applications(self.conn, archived=True), [])

    def test_legacy_stage_migration_and_options(self):
        annotations = db.annotations_for(self.conn, [self.key])
        for stage in ('test', 'interview'):
            self.conn.execute('UPDATE stars SET stage=? WHERE key=?', (stage, self.key))
            db.init(self.conn)
            db.init(self.conn)
            self.assertEqual(self.conn.execute('SELECT stage FROM stars WHERE key=?', (self.key,)).fetchone()[0], 'applied')
            self.assertEqual(db.annotations_for(self.conn, [self.key]), annotations)
            self.assertFalse(app.api_stage(self.conn, {'key': self.key, 'stage': stage})['ok'])
        html = app.page_applications(self.conn, {}).decode()
        self.assertIn('value="applied"', html)
        self.assertIn('value="closed"', html)
        self.assertNotIn('value="test"', html)
        self.assertNotIn('value="interview"', html)


if __name__ == '__main__':
    unittest.main()
