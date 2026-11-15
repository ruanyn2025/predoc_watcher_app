import sqlite3
import sys
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app
import db
import i18n
import ingest


class ManualJobsTest(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(':memory:')
        self.conn.row_factory = sqlite3.Row
        db.init(self.conn)

    def tearDown(self):
        self.conn.close()

    def add(self, **fields):
        return db.add_manual_job(self.conn, dict(title='Research assistant', **fields))

    def test_add_search_and_unique_keys(self):
        key = self.add(institution='Example University', fields='Labor')
        other = self.add()
        self.assertNotEqual(key, other)
        rows = db.search_jobs(self.conn, q='Labor Example', source='manual')
        self.assertEqual([r['key'] for r in rows], [key])
        self.assertEqual(rows[0]['status'], 'open')
        self.assertEqual(db.unread_jobs(self.conn), [])
        self.assertFalse(db.is_initialized(self.conn))

    def test_validation(self):
        for payload in ({'title': ' '}, {'title': []}, {'title': 'x' * 2001},
                        {'title': 'x', 'link': 'javascript:alert(1)'},
                        {'title': 'x', 'link': 'https://'},
                        {'title': 'x', 'link': 'https://['}):
            with self.subTest(payload=payload):
                self.assertFalse(app.api_manual_add(self.conn, payload)['ok'])
        self.assertFalse(app.api_manual_add(self.conn, [])['ok'])
        self.assertFalse(app.api_manual_delete(self.conn, {})['ok'])
        self.assertEqual(db.stats(self.conn)['total'], 0)
        self.add(link='https://example.org/job')

    def test_lifecycle_and_delete(self):
        key = self.add()
        today = date.today().isoformat()
        db.star(self.conn, key, today, 'manual')
        db.add_annotation(self.conn, key, 'event', label='Interview', on_date=today)
        self.assertEqual(len(db.starred_jobs(self.conn)), 1)
        self.assertEqual(len(db.reminders_between(self.conn, today, today)), 1)
        db.mark_applied(self.conn, key)
        self.assertEqual(len(db.applications(self.conn)), 1)
        self.assertEqual(len(db.applied_between(self.conn, today, today)), 1)
        self.assertTrue(app.api_manual_delete(self.conn, {'key': key})['ok'])
        for table in ('jobs', 'stars', 'annotations'):
            self.assertEqual(self.conn.execute('SELECT COUNT(*) FROM ' + table).fetchone()[0], 0)
        self.assertEqual(db.annotation_events_between(self.conn, today, today), [])
        self.assertFalse(app.api_manual_delete(self.conn, {'key': key})['ok'])

    def test_refresh_isolation_and_fetched_delete_guard(self):
        key = self.add()
        results = {'predoc': {'ok': True, 'items': [{'title': 'Fetched', 'link': 'https://example.org'}]}}
        with patch.object(ingest.fetch, 'collect_all', return_value=results):
            ingest.refresh(self.conn)
        fetched = db.search_jobs(self.conn, source='predoc')[0]
        self.assertEqual(fetched['unread'], 0)
        self.assertFalse(app.api_manual_delete(self.conn, {'key': fetched['key']})['ok'])
        self.assertIsNotNone(db.get_job(self.conn, fetched['key']))
        self.assertEqual(db.get_job(self.conn, key)['status'], 'open')
        db.delete_manual_job(self.conn, key)
        with patch.object(ingest.fetch, 'collect_all', return_value=results):
            ingest.refresh(self.conn)
        self.assertIsNone(db.get_job(self.conn, key))

    def test_pages_in_all_languages(self):
        key = db.add_manual_job(self.conn, {'title': '<script>alert(1)</script>'})
        db.star(self.conn, key, date.today().isoformat(), 'manual')
        for lang in i18n.LANGS:
            db.set_meta(self.conn, 'lang', lang)
            form = app.page_manual(self.conn, {}).decode()
            self.assertIn('name="title"', form)
            self.assertNotIn('>manual.hint<', form)
            for page in (app.page_history, app.page_starred):
                html = page(self.conn, {}).decode()
                self.assertIn('deleteManualJob(this)', html)
                self.assertIn('&lt;script&gt;', html)
                self.assertNotIn('href=""', html)
            self.assertIn('manual.confirm_delete', i18n.js_strings(lang))
        db.mark_applied(self.conn, key)
        self.assertIn('deleteManualJob(this)', app.page_applications(self.conn, {}).decode())


if __name__ == '__main__':
    unittest.main()
