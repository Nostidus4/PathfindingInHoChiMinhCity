"""TV6: Visualize GA optimization and room occupancy. No mocked results in production."""
from __future__ import annotations
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
from src import config as C
from src.chromosome import decode
from src.data_generator import Instance


def plot_history(history: list[dict], path: str) -> None:
    """Plot best/average penalty and hard violations from real GA history."""
    if not history:
        raise ValueError('history must not be empty')
    required = {'gen', 'best_penalty', 'avg_penalty', 'hard_best'}
    for i, record in enumerate(history):
        missing = required.difference(record)
        if missing:
            raise ValueError(f'history[{i}] missing keys: {sorted(missing)}')
    generations = np.asarray([r['gen'] for r in history], dtype=float)
    best = np.asarray([r['best_penalty'] for r in history], dtype=float)
    avg = np.asarray([r['avg_penalty'] for r in history], dtype=float)
    hard = np.asarray([r['hard_best'] for r in history], dtype=float)
    if not (np.isfinite(generations).all() and np.isfinite(best).all() and np.isfinite(avg).all() and np.isfinite(hard).all()):
        raise ValueError('history contains non-finite values')
    if (best < 0).any() or (avg < 0).any() or (hard < 0).any():
        raise ValueError('penalty and hard violations must be nonnegative')
    dest = Path(path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    fig, left = plt.subplots(figsize=(11, 6))
    l1, = left.plot(generations, best, label='Best penalty', lw=2.2, color='#2057b2')
    l2, = left.plot(generations, avg, label='Average penalty', lw=1.8, color='#e59c35', alpha=.9)
    left.set_yscale('symlog', linthresh=1)  # supports true zero unlike log
    left.set_xlabel('Generation')
    left.set_ylabel('Penalty (symmetric log scale)')
    left.grid(alpha=.2, which='both')
    right = left.twinx()
    l3, = right.plot(generations, hard, label='Hard violations (best)', lw=1.8, color='#ba3553', linestyle='--')
    right.set_ylabel('Number of hard violations')
    right.set_ylim(bottom=0)
    left.legend([l1, l2, l3], [x.get_label() for x in (l1,l2,l3)], loc='upper right')
    fig.suptitle('Genetic Algorithm - Optimization History', fontsize=14, weight='bold')
    fig.tight_layout()
    fig.savefig(dest, dpi=180, bbox_inches='tight')
    plt.close(fig)


def plot_room_heatmap(chrom: np.ndarray, inst: Instance, path: str) -> None:
    """Rows=rooms, columns=day/slot. Gray unavailable, blue occupied, red conflicts."""
    sessions = decode(np.asarray(chrom))
    counts = np.zeros((inst.n_rooms, C.N_DAYS, C.N_SLOTS), dtype=int)
    for _, day, slot, room, _ in sessions:
        counts[int(room), int(day), int(slot)] += 1
    state = np.where(~np.asarray(inst.room_avail, dtype=bool), 3,
                     np.where(counts >= 2, 2, np.where(counts == 1, 1, 0)))
    # Any occupied unavailable cell is still marked unavailable and is also noted by count overlay.
    matrix = state.reshape(inst.n_rooms, C.N_DAYS * C.N_SLOTS)
    fig, ax = plt.subplots(figsize=(13, max(5, inst.n_rooms * .32 + 2)))
    cmap = ListedColormap(['#f2f5f9', '#68a5da', '#e76a70', '#808a96'])
    ax.imshow(matrix, aspect='auto', interpolation='nearest', cmap=cmap,
              norm=BoundaryNorm([-.5,.5,1.5,2.5,3.5], 4))
    ax.set_xticks(np.arange(C.N_DAYS * C.N_SLOTS))
    ax.set_xticklabels([f'{C.DAY_NAMES[d]}-{s+1}' for d in range(C.N_DAYS) for s in range(C.N_SLOTS)], rotation=65, ha='right', fontsize=8)
    ax.set_yticks(np.arange(inst.n_rooms))
    ax.set_yticklabels([f'Room {r+1}' for r in range(inst.n_rooms)], fontsize=8)
    for d in range(1, C.N_DAYS):
        ax.axvline(d * C.N_SLOTS - .5, color='#3c4b65', lw=1.2)
    ax.set_title('Room occupancy - gray: unavailable; red: 2+ sessions', fontweight='bold')
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=c, label=t) for c,t in zip(cmap.colors, ['Empty','One session','Conflict (2+)','Unavailable'])], ncol=4, loc='upper center', bbox_to_anchor=(.5,-.15), fontsize=9)
    fig.tight_layout()
    dest=Path(path); dest.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(dest, dpi=180, bbox_inches='tight')
    plt.close(fig)
