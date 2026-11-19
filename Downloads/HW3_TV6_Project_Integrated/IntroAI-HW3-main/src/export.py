"""TV6: export one row per teaching session into CSV, Excel and a browsable HTML timetable."""
from __future__ import annotations
from collections import Counter
from html import escape
from pathlib import Path
import numpy as np
import pandas as pd
from src import config as C
from src.chromosome import decode
from src.data_generator import Instance


COLUMNS = ['course', 'section', 'session', 'day', 'slot', 'room', 'prof', 'reg', 'room_size',
           'room_conflict', 'prof_conflict', 'room_unavailable', 'undersized_room', 'conflict']


def schedule_dataframe(chrom: np.ndarray, inst: Instance) -> pd.DataFrame:
    """Build 960-row (for default config) table with explicit conflict flags.

    Human-facing IDs start at 1, day names are T2..T6, slots are 1..6.
    """
    chrom = np.asarray(chrom)
    if chrom.shape != (inst.n_sections, C.N_GENE_FIELDS):
        raise ValueError(f'Expected chromosome shape {(inst.n_sections, C.N_GENE_FIELDS)}, got {chrom.shape}')
    ses = decode(chrom)
    if ((ses[:, 1] < 0) | (ses[:, 1] >= C.N_DAYS) | (ses[:, 2] < 0) | (ses[:, 2] >= C.N_SLOTS) |
        (ses[:, 3] < 0) | (ses[:, 3] >= inst.n_rooms) | (ses[:, 4] < 0) | (ses[:, 4] >= inst.n_profs)).any():
        raise ValueError('Decoded chromosome contains out-of-range day/slot/room/prof IDs')
    sections, days, slots, rooms, profs = (ses[:, j].astype(int) for j in range(5))
    room_count = Counter(zip(rooms, days, slots))
    prof_count = Counter(zip(profs, days, slots))
    rsize = np.asarray(inst.room_size)[rooms]
    reg = np.asarray(inst.sec_reg)[sections]
    room_conflict = np.asarray([room_count[k] > 1 for k in zip(rooms, days, slots)])
    prof_conflict = np.asarray([prof_count[k] > 1 for k in zip(profs, days, slots)])
    unavailable = ~np.asarray(inst.room_avail, dtype=bool)[rooms, days, slots]
    undersized = rsize < reg
    result = pd.DataFrame({
        'course': np.asarray(inst.sec_course)[sections] + 1,
        'section': sections + 1,
        'session': np.tile([1, 2], len(chrom)),
        'day': np.asarray(C.DAY_NAMES)[days],
        'slot': slots + 1,
        'room': rooms + 1,
        'prof': profs + 1,
        'reg': reg, 'room_size': rsize,
        'room_conflict': room_conflict, 'prof_conflict': prof_conflict,
        'room_unavailable': unavailable, 'undersized_room': undersized,
    })
    result['conflict'] = result[['room_conflict','prof_conflict','room_unavailable','undersized_room']].any(axis=1)
    return result[COLUMNS].sort_values(['day','slot','room','section'], key=lambda s: s.map({d:i for i,d in enumerate(C.DAY_NAMES)}) if s.name=='day' else s, kind='stable').reset_index(drop=True)


def export_schedule(chrom: np.ndarray, inst: Instance, folder: str) -> None:
    """Generate schedule.csv / schedule.xlsx / schedule.html with room/prof/day views."""
    target = Path(folder)
    target.mkdir(parents=True, exist_ok=True)
    df = schedule_dataframe(chrom, inst)
    df.to_csv(target / 'schedule.csv', index=False, encoding='utf-8-sig')
    with pd.ExcelWriter(target / 'schedule.xlsx', engine='openpyxl') as writer:
        for name, col in [('By Room', 'room'), ('By Professor', 'prof'), ('By Day', 'day')]:
            order = [col, 'day', 'slot'] if col != 'day' else ['day', 'slot', 'room']
            sdf = df.sort_values(order, key=lambda s: s.map({d:i for i,d in enumerate(C.DAY_NAMES)}) if s.name=='day' else s)
            sdf.to_excel(writer, sheet_name=name, index=False)
            ws = writer.sheets[name]
            ws.freeze_panes = 'A2'
            ws.auto_filter.ref = ws.dimensions
            from openpyxl.styles import Font, PatternFill, Alignment
            for cell in ws[1]:
                cell.font = Font(bold=True, color='FFFFFF')
                cell.fill = PatternFill('solid', fgColor='1B355F')
                cell.alignment = Alignment(horizontal='center')
            for row in ws.iter_rows(min_row=2):
                if row[-1].value:
                    for c in row:
                        c.fill = PatternFill('solid', fgColor='FCE4E4')
            for column in ws.columns:
                letter = column[0].column_letter
                ws.column_dimensions[letter].width = min(24, max(11, max(len(str(c.value or '')) for c in list(column)[:150]) + 2))
    (target / 'schedule.html').write_text(_render_html(df, inst), encoding='utf-8')


def _render_html(df: pd.DataFrame, inst: Instance) -> str:
    def cell_text(sub: pd.DataFrame) -> str:
        if sub.empty: return '<span class="empty">—</span>'
        pieces = []
        for row in sub.itertuples(index=False):
            name = f'C{row.course:02d} / S{row.section:03d} / P{row.prof:02d} / R{row.room:02d}'
            tips = ', '.join(k for k in ('room_conflict','prof_conflict','room_unavailable','undersized_room') if getattr(row,k))
            pieces.append(f'<span class="event {"bad" if row.conflict else "ok"}" title="{escape(tips or "No conflict")}">{escape(name)}</span>')
        return ''.join(pieces)

    def grid(group_col: str, group_val: int | None) -> str:
        data = df if group_val is None else df[df[group_col] == group_val]
        head = '<tr><th>Slot</th>' + ''.join(f'<th>{d}</th>' for d in C.DAY_NAMES) + '</tr>'
        rows=[]
        for slot in range(1, C.N_SLOTS+1):
            cells = ''.join(f'<td>{cell_text(data[(data.day==day)&(data.slot==slot)])}</td>' for day in C.DAY_NAMES)
            rows.append(f'<tr><th>{slot}</th>{cells}</tr>')
        return '<table class="timetable">'+head+''.join(rows)+'</table>'

    views = [('overview','Overview',grid('',None))]
    for room in range(1,inst.n_rooms+1):
        views.append((f'room-{room}', f'Room {room}',grid('room',room)))
    for prof in sorted(df['prof'].unique()):
        views.append((f'prof-{prof}', f'Professor {prof}',grid('prof',int(prof))))
    # The overview is explicitly the day/slot view; filtered room and professor views give the others.
    options=''.join(f'<option value="{escape(i)}">{escape(title)}</option>' for i,title,_ in views)
    sections=''.join(f'<section id="{escape(i)}" class="view" style="display:{"block" if j==0 else "none"}"><h2>{escape(title)}</h2>{table}</section>' for j,(i,title,table) in enumerate(views))
    conflicts=int(df['conflict'].sum())
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>CO3061 - Schedule</title>
<style>
:root{{--navy:#132b4a;--blue:#3e7abd;--red:#b9273c}}*{{box-sizing:border-box}}body{{margin:0;font:14px/1.5 system-ui,Arial,sans-serif;color:#233047;background:#f3f6fb}}header{{background:var(--navy);color:white;padding:24px max(20px,calc((100vw - 1400px)/2))}}main{{max-width:1400px;margin:24px auto;padding:0 20px}}h1{{margin:0 0 5px}}h2{{font-size:19px}}.stats{{display:flex;gap:15px;flex-wrap:wrap;margin:15px 0 20px}}.stat{{background:white;padding:14px 18px;border-radius:8px;box-shadow:0 1px 6px #dce3ee}}select{{padding:9px 12px;margin-bottom:15px;border:1px solid #a0acc0;border-radius:6px;max-width:100%}}.view{{overflow-x:auto}}.timetable{{border-collapse:collapse;table-layout:fixed;width:100%;background:white}}th,td{{border:1px solid #dce4f0;padding:9px;vertical-align:top;min-width:135px}}th{{background:#e4eaf5}}.event{{display:block;border-radius:5px;margin-bottom:5px;padding:5px 7px;font-size:12px;overflow-wrap:anywhere}}.ok{{background:#d9ecff;border-left:3px solid var(--blue)}}.bad{{background:#ffe0e5;border-left:3px solid var(--red)}}.empty{{color:#a0a9bb}}footer{{padding:20px;color:#687990}}
</style></head><body><header><h1>Class Scheduling · Genetic Algorithm</h1><div>CO3061 · Monday–Friday · 6 timeslots per day</div></header>
<main><div class="stats"><div class="stat"><b>{len(df)}</b> scheduled sessions</div><div class="stat"><b>{inst.n_sections}</b> sections</div><div class="stat"><b>{inst.n_rooms}</b> rooms</div><div class="stat"><b>{conflicts}</b> sessions flagged (may overlap across violation types)</div></div><label for="view-select">Choose view: </label><select id="view-select" onchange="document.querySelectorAll('.view').forEach(e=>e.style.display=e.id===this.value?'block':'none')">{options}</select>{sections}</main><footer>Blue = no listed room/professor/capacity/availability conflict; red = at least one flagged violation. IDs are 1-based. This schedule is not guaranteed feasible.</footer></body></html>'''
