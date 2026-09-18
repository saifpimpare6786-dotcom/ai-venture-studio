import sqlite3
import json

conn = sqlite3.connect('data/venture_studio.db')
cursor = conn.cursor()
cursor.execute('SELECT id, name, overall_score, viability_score, market_fit_score, financial_score FROM projects')
projects = {row[0]: row for row in cursor.fetchall()}

cursor.execute('SELECT id, project_id, content FROM reports WHERE report_type = "investment_readiness"')
reports = cursor.fetchall()

updated = 0
for rep_id, pid, content_str in reports:
    if pid not in projects:
        continue
    p = projects[pid]
    p_name, p_overall, p_viab, p_mkt, p_fin = p[1], p[2], p[3], p[4], p[5]
    c = json.loads(content_str)
    sb = c.get('scoring_breakdown')
    if sb and isinstance(sb, dict):
        if (sb.get('viability_score') != p_viab or 
            sb.get('market_fit_score') != p_mkt or 
            sb.get('financial_score') != p_fin or 
            sb.get('overall_score') != p_overall):
            print(f"Syncing project {pid} ({p_name}):")
            print(f"  Old: viab={sb.get('viability_score')}, mkt={sb.get('market_fit_score')}, fin={sb.get('financial_score')} => {sb.get('overall_score')}")
            print(f"  New: viab={p_viab}, mkt={p_mkt}, fin={p_fin} => {p_overall}")
            sb['viability_score'] = p_viab
            sb['market_fit_score'] = p_mkt
            sb['financial_score'] = p_fin
            sb['overall_score'] = p_overall
            c['scoring_breakdown'] = sb
            cursor.execute('UPDATE reports SET content = ? WHERE id = ?', (json.dumps(c, ensure_ascii=True), rep_id))
            updated += 1

conn.commit()
conn.close()
print(f"Done. Updated {updated} investment_readiness reports in DB.")
