"""TV6 integration tests against the repo's public interfaces and mock fixtures."""
import pandas as pd
import numpy as np
import pytest
from src.visualize import plot_history, plot_room_heatmap
from src.export import export_schedule, schedule_dataframe
from src._mocks import fake_history, fake_instance, fake_chromosome


def test_plot_history_writes_png(tmp_path):
    dest=tmp_path/'plots'/'fitness.png'
    plot_history(fake_history(20), str(dest))
    assert dest.is_file() and dest.stat().st_size>2000


def test_plot_history_rejects_missing_fields(tmp_path):
    with pytest.raises(ValueError, match='missing keys'):
        plot_history([{'gen':0}], str(tmp_path/'plot.png'))


def test_plot_history_handles_zero_hard(tmp_path):
    plot_history([{'gen':0,'best_penalty':0,'avg_penalty':0,'hard_best':0}], str(tmp_path/'zero.png'))
    assert (tmp_path/'zero.png').exists()


def test_room_heatmap(tmp_path):
    rng=np.random.default_rng(3); inst=fake_instance(8,3)
    plot_room_heatmap(fake_chromosome(inst,rng),inst,str(tmp_path/'fig'/'rooms.png'))
    assert (tmp_path/'fig'/'rooms.png').stat().st_size>2000


def test_export_all_formats(tmp_path):
    rng=np.random.default_rng(3); inst=fake_instance(8,3)
    chrom=fake_chromosome(inst,rng)
    export_schedule(chrom,inst,str(tmp_path/'nested'))
    folder=tmp_path/'nested'
    for name in ['schedule.csv','schedule.xlsx','schedule.html']:
        assert (folder/name).stat().st_size>0
    df=pd.read_csv(folder/'schedule.csv')
    assert len(df)==inst.n_sections*2
    assert set(['course','section','session','day','slot','room','prof','reg','room_size','conflict']).issubset(df.columns)
    assert set(df['session'])=={1,2}
    assert set(df['day']).issubset({'T2','T3','T4','T5','T6'})
    assert set(pd.ExcelFile(folder/'schedule.xlsx').sheet_names)=={'By Room','By Professor','By Day'}
    html=(folder/'schedule.html').read_text(encoding='utf8')
    assert '<table' in html and 'Room 1' in html and 'Professor' in html and 'bad' in html


def test_conflict_flags(tmp_path):
    inst=fake_instance(3,3)
    inst.room_size[:]=2
    inst.sec_reg[:]=0
    inst.room_avail[:]=True
    chrom=np.zeros((inst.n_sections,6), dtype=int)
    # All sections share professor 0, rooms 0, and the same two sessions.
    df=schedule_dataframe(chrom,inst)
    assert df['room_conflict'].all() and df['prof_conflict'].all()
    inst.room_avail[0,0,0]=False
    df=schedule_dataframe(chrom,inst)
    assert df.loc[df.day=='T2','room_unavailable'].all()


def test_bad_shape(tmp_path):
    inst=fake_instance(3,3)
    with pytest.raises(ValueError,match='shape'):
        export_schedule(np.zeros((1,6),dtype=int),inst,str(tmp_path))
