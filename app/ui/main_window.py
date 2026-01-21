from __future__ import annotations

import json
import os
from pathlib import Path

from PySide6 import QtCore, QtGui, QtWidgets

from app.models.entities import AppState, Track, PlaylistItem, ScheduleEvent, ScheduleStreamBlock
from app.services.ids import new_id
from app.services.storage import save_state_to_file, load_state_from_file
from app.services.audio_metadata import read_audio_metadata
from app.services.player import AudioPlayer

from app.ui.styles import APP_QSS
from app.ui.widgets.left_panel import LeftPanel
from app.ui.widgets.schedule_panel import SchedulePanel
from app.ui.widgets.popovers import SchedulePopover, StreamSelectPopover
from app.ui.widgets.footer import FooterBar
from app.ui.widgets.drawer import DrawerPanel
from app.ui.tabs import AudioFileTab, SpotifyTab, DynamicTextsTab, StreamsTab, SettingsTab


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Rádio Kája Jižák')

        # App state
        self.state = AppState()
        self.player = AudioPlayer()
        self.player.on_track_end = self._on_track_end
        self._active_popover = None

        # Root
        root = QtWidgets.QWidget()
        self.setCentralWidget(root)
        v = QtWidgets.QVBoxLayout(root)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        # Header
        self.header = QtWidgets.QFrame(); self.header.setObjectName('HeaderBar')
        hv = QtWidgets.QHBoxLayout(self.header)
        hv.setContentsMargins(12, 10, 12, 10)
        hv.setSpacing(10)

        # Logo + title
        self.logo = QtWidgets.QLabel()
        self.logo.setFixedSize(36, 36)
        self.logo.setScaledContents(True)
        self.title = QtWidgets.QLabel('Rádio Kája Jižák')
        self.title.setObjectName('HeaderTitle')
        left = QtWidgets.QHBoxLayout()
        left.addWidget(self.logo)
        left.addWidget(self.title)
        leftw = QtWidgets.QWidget(); leftw.setLayout(left)

        self.tabbar = QtWidgets.QTabBar()
        self.tabbar.addTab('AudioFile')
        self.tabbar.addTab('Spotify')
        self.tabbar.addTab('Dynamické texty')
        self.tabbar.addTab('STREAMY')
        self.tabbar.addTab('Nastavení')
        self.tabbar.setExpanding(False)

        self.btn_load = QtWidgets.QPushButton('LOAD')
        self.btn_save = QtWidgets.QPushButton('SAVE'); self.btn_save.setObjectName('Primary')
        self.btn_exit = QtWidgets.QPushButton('EXIT')

        hv.addWidget(leftw)
        hv.addStretch(1)
        hv.addWidget(self.tabbar)
        hv.addStretch(1)
        hv.addWidget(self.btn_load)
        hv.addWidget(self.btn_save)
        hv.addWidget(self.btn_exit)

        # Panorama line
        self.panoline = QtWidgets.QFrame(); self.panoline.setObjectName('PanoramaLine')
        self.panoline.setFixedHeight(2)

        # Workspace
        self.split = QtWidgets.QSplitter(QtCore.Qt.Horizontal)

        self.left_panel = LeftPanel()
        self.schedule_panel = SchedulePanel()
        # convenience handle
        self.canvas = self.schedule_panel.canvas
        self.drawer = DrawerPanel()

        # Right side container: canvas + drawer
        right = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        right.addWidget(self.schedule_panel)
        right.addWidget(self.drawer)
        right.setStretchFactor(0, 4)
        right.setStretchFactor(1, 1)

        self.split.addWidget(self.left_panel)
        self.split.addWidget(right)
        self.split.setStretchFactor(0, 1)
        self.split.setStretchFactor(1, 3)

        # Footer
        self.footer = FooterBar()

        v.addWidget(self.header)
        v.addWidget(self.panoline)
        v.addWidget(self.split, 1)
        v.addWidget(self.footer)

        # Tabs (stack)
        self.stack = QtWidgets.QStackedWidget()
        self.tab_audio = AudioFileTab()
        self.tab_spotify = SpotifyTab()
        self.tab_texts = DynamicTextsTab()
        self.tab_streams = StreamsTab()
        self.tab_settings = SettingsTab()

        self.stack.addWidget(self.tab_audio)
        self.stack.addWidget(self.tab_spotify)
        self.stack.addWidget(self.tab_texts)
        self.stack.addWidget(self.tab_streams)
        self.stack.addWidget(self.tab_settings)

        # Insert stack as overlay on canvas? Keep simple: show stack in a dock-like window.
        self.dock = QtWidgets.QDockWidget('Správa/konfigurace', self)
        self.dock.setWidget(self.stack)
        self.addDockWidget(QtCore.Qt.TopDockWidgetArea, self.dock)
        self.dock.setAllowedAreas(QtCore.Qt.TopDockWidgetArea)
        self.dock.setFeatures(QtWidgets.QDockWidget.DockWidgetMovable)

        # Signals
        self.tabbar.currentChanged.connect(self.stack.setCurrentIndex)
        self.btn_exit.clicked.connect(self.close)
        self.btn_save.clicked.connect(self._save)
        self.btn_load.clicked.connect(self._load)

        self.tab_audio.importFilesClicked.connect(self._import_audio_files)
        self.tab_audio.scanFolderClicked.connect(self._scan_audio_folder)

        self.left_panel.addToPlaylistRequested.connect(self._add_to_playlist)
        self.left_panel.deleteRequested.connect(self._delete_item)
        self.left_panel.infoRequested.connect(self._show_info)

        # Use *_At signals so we can place popovers at the drop/draw location.
        self.canvas.eventDroppedAt.connect(self._on_canvas_drop_at)
        self.canvas.streamBlockDrawnAt.connect(self._on_canvas_stream_draw_at)

        self.footer.playClicked.connect(self._play)
        self.footer.stopClicked.connect(self._stop)
        self.footer.muteToggled.connect(self._mute)
        self.footer.volumeChanged.connect(self.player.set_volume)
        self.footer.boostToggled.connect(self._boost)
        self.footer.hotkeyPressed.connect(self._hotkey)

        self.tab_settings.settingsChanged.connect(self._on_settings_changed)

        # UI init
        self._apply_style()
        self._load_logo()
        self._refresh_all()

        # Meter update
        self._meter_timer = QtCore.QTimer(self)
        self._meter_timer.timeout.connect(self._update_meters)
        self._meter_timer.start(33)

    def _apply_style(self):
        self.setStyleSheet(APP_QSS)

    def _load_logo(self):
        # Required logo path (from spec). If not found, keep blank.
        candidates = [
            Path('/mnt/data/logo_radiopng'),
            Path('logo_radiopng'),
            Path('app/resources/logo.png'),
        ]
        for p in candidates:
            if p.exists():
                pm = QtGui.QPixmap(str(p))
                if not pm.isNull():
                    self.logo.setPixmap(pm)
                    return
        # fallback: text
        self.logo.setText('◉')
        self.logo.setStyleSheet('color:#F4C61C; font-size: 18px; font-weight: 700;')
        self.logo.setAlignment(QtCore.Qt.AlignCenter)

    def _refresh_all(self):
        # Left panel lists
        track_items = []
        for t in self.state.tracks:
            label = f"{t.title} — {t.artist} ({t.duration_sec}s)"
            track_items.append((t.id, label, t.source))
        self.left_panel.set_tracks(track_items)

        text_items = [(dt.id, dt.name) for dt in self.state.dynamic_texts]
        self.left_panel.set_dynamic_texts(text_items)

        playlist_items = []
        for it in self.state.playlist:
            label = self._label_for_ref(it.item_type, it.ref_id)
            playlist_items.append((it.item_type, it.ref_id, label))
        self.left_panel.set_playlist(playlist_items)

        # Canvas data
        events = []
        for e in self.state.schedule_events:
            h, m = map(int, e.time_hhmm.split(':'))
            minute = h*60 + m
            events.append({'id': e.id, 'day_index': e.day_index, 'minute': minute, 'label': self._label_for_ref(e.item_type, e.ref_id)})
        streams = []
        for b in self.state.schedule_stream_blocks:
            sh, sm = map(int, b.start_hhmm.split(':'))
            eh, em = map(int, b.end_hhmm.split(':'))
            streams.append({'id': b.id, 'day_index': b.day_index, 'start_min': sh*60+sm, 'end_min': eh*60+em})
        self.canvas.set_data(events, streams)

        # Hotkey labels
        labels = []
        for hk in self.state.hotkeys:
            if hk.item_type and hk.ref_id:
                labels.append(hk.label or self._label_for_ref(hk.item_type, hk.ref_id)[:8])
            else:
                labels.append('')
        self.footer.set_hotkey_labels(labels)

        # Settings tab
        self.tab_settings.set_values(self.state.settings.__dict__)

        # Playlist warning
        if not self.state.playlist:
            self.statusBar().showMessage('Playlist je prázdný: přetáhni track do playlistu (levý panel → Aktuální playlist).')
        else:
            self.statusBar().clearMessage()

    def _label_for_ref(self, item_type: str, ref_id: str) -> str:
        if item_type in ('audiofile', 'spotify'):
            for t in self.state.tracks:
                if t.id == ref_id:
                    return f"{t.title} — {t.artist}"
        if item_type == 'dynamic_text':
            for d in self.state.dynamic_texts:
                if d.id == ref_id:
                    return f"Hláška: {d.name}"
        if item_type == 'stream':
            for s in self.state.streams:
                if s.id == ref_id:
                    return f"Stream: {s.name}"
        return f"{item_type}:{ref_id}"

    # SAVE / LOAD
    def _save(self):
        fp, _ = QtWidgets.QFileDialog.getSaveFileName(self, 'SAVE konfigurace', '', 'JSON (*.json)')
        if not fp:
            return
        save_state_to_file(self.state, fp)
        self.statusBar().showMessage(f'Uloženo: {fp}', 5000)

    def _load(self):
        fp, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'LOAD konfigurace', '', 'JSON (*.json)')
        if not fp:
            return
        try:
            self.state = load_state_from_file(fp)
            self.statusBar().showMessage(f'Načteno: {fp}', 5000)
            self._refresh_all()
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, 'LOAD chyba', str(e))

    # AudioFile import
    def _import_audio_files(self):
        files, _ = QtWidgets.QFileDialog.getOpenFileNames(self, 'Vyber audio soubory', '', 'Audio (*.mp3 *.wav *.flac *.ogg *.m4a);;All (*.*)')
        if not files:
            return
        for f in files:
            self._add_audiofile_track(f)
        self._refresh_all()

    def _scan_audio_folder(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(self, 'Vyber adresář k prohledání')
        if not folder:
            return
        exts = {'.mp3', '.wav', '.flac', '.ogg', '.m4a'}
        for p in Path(folder).rglob('*'):
            if p.suffix.lower() in exts:
                self._add_audiofile_track(str(p))
        self._refresh_all()

    def _add_audiofile_track(self, path: str):
        meta = read_audio_metadata(path)
        if not meta:
            return
        # Avoid duplicates by path
        for t in self.state.tracks:
            if t.source == 'audiofile' and t.path == path:
                return
        self.state.tracks.append(Track(
            id=new_id('trk'),
            source='audiofile',
            title=meta.title,
            artist=meta.artist,
            duration_sec=meta.duration_sec,
            path=path,
        ))

    # Left panel actions
    def _add_to_playlist(self, item_type: str, ref_id: str):
        if len(self.state.playlist) >= 50:
            QtWidgets.QMessageBox.warning(self, 'Playlist', 'Playlist má limit 50 prvků.')
            return
        # Only allow elements that exist in internal DB (rule)
        if not self._exists(item_type, ref_id):
            return
        self.state.playlist.append(PlaylistItem(item_type=item_type, ref_id=ref_id))
        self._refresh_all()

    def _delete_item(self, item_type: str, ref_id: str):
        # Remove from DB + playlist + schedule + hotkeys
        if item_type in ('audiofile', 'spotify'):
            self.state.tracks = [t for t in self.state.tracks if t.id != ref_id]
        elif item_type == 'dynamic_text':
            self.state.dynamic_texts = [d for d in self.state.dynamic_texts if d.id != ref_id]
        elif item_type == 'stream':
            self.state.streams = [s for s in self.state.streams if s.id != ref_id]

        self.state.playlist = [p for p in self.state.playlist if p.ref_id != ref_id]
        self.state.schedule_events = [e for e in self.state.schedule_events if e.ref_id != ref_id]
        self.state.schedule_stream_blocks = [b for b in self.state.schedule_stream_blocks if b.stream_id != ref_id]
        for hk in self.state.hotkeys:
            if hk.ref_id == ref_id:
                hk.item_type = None
                hk.ref_id = None
                hk.label = ''

        self._refresh_all()

    def _show_info(self, item_type: str, ref_id: str):
        self.drawer.set_content('Info', self._label_for_ref(item_type, ref_id))

    def _close_active_popover(self) -> None:
        p = getattr(self, "_active_popover", None)
        if p is not None:
            try:
                p.close()
            except Exception:
                pass
        self._active_popover = None

    def _show_popover(self, pop: QtWidgets.QWidget) -> None:
        self._close_active_popover()
        self._active_popover = pop
        pop.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
        pop.destroyed.connect(lambda *_: setattr(self, "_active_popover", None))
        pop.show()

    # Canvas planning (popover flows; no heavy dialogs)
    def _on_canvas_drop_at(self, day_index: int, hhmm: str, item_type: str, ref_id: str, global_pos: QtCore.QPoint):
        if not self._exists(item_type, ref_id):
            QtWidgets.QMessageBox.warning(self, 'Plán', 'Prvek není v interní databázi aplikace.')
            return
        label = self._label_for_ref(item_type, ref_id)
        pop = SchedulePopover(
            title="Naplánovat",
            subtitle=label,
            initial_day_index=day_index,
            initial_hhmm=hhmm,
            parent=self,
        )

        def _accept(days: list[int], hhmm2: str):
            # one drag = one time; possibly multiple days
            for di in days:
                self.state.schedule_events.append(ScheduleEvent(
                    id=new_id('ev'),
                    day_index=di,
                    time_hhmm=hhmm2,
                    item_type=item_type,
                    ref_id=ref_id,
                ))
            self._refresh_all()
            dnames = ['Po','Út','St','Čt','Pá','So','Ne']
            days_str = ", ".join(dnames[d] for d in days)
            self.drawer.set_content('Naplánováno', f"{hhmm2} / {days_str}\n{label}")
            self._close_active_popover()

        def _reject():
            self._close_active_popover()

        pop.acceptedDaysTime.connect(_accept)
        pop.rejected.connect(_reject)
        pop.show_at(global_pos)
        self._show_popover(pop)

    def _on_canvas_stream_draw_at(self, day_index: int, start_hhmm: str, end_hhmm: str, global_pos: QtCore.QPoint):
        if not self.state.streams:
            QtWidgets.QMessageBox.warning(self, 'Stream', 'Nejsou vybrané žádné streamy v databázi. Nejprve přidej stream do karty STREAMY.')
            return
        streams = [(s.id, s.name) for s in self.state.streams]
        pop = StreamSelectPopover(
            title="Vybrat stream",
            subtitle=f"{start_hhmm}–{end_hhmm} / {['Po','Út','St','Čt','Pá','So','Ne'][day_index]}",
            streams=streams,
            parent=self,
        )

        def _accept(stream_id: str):
            stream = next((s for s in self.state.streams if s.id == stream_id), None)
            if not stream:
                self._close_active_popover()
                return
            self.state.schedule_stream_blocks.append(ScheduleStreamBlock(
                id=new_id('sb'),
                day_index=day_index,
                start_hhmm=start_hhmm,
                end_hhmm=end_hhmm,
                stream_id=stream.id,
            ))
            self._refresh_all()
            self.drawer.set_content('Stream blok', f"{start_hhmm}–{end_hhmm} / {['Po','Út','St','Čt','Pá','So','Ne'][day_index]}\nStream: {stream.name}")
            self._close_active_popover()

        def _reject():
            self._close_active_popover()

        pop.acceptedStream.connect(_accept)
        pop.rejected.connect(_reject)
        pop.show_at(global_pos)
        self._show_popover(pop)

    def _exists(self, item_type: str, ref_id: str) -> bool:
        if item_type in ('audiofile', 'spotify'):
            return any(t.id == ref_id for t in self.state.tracks)
        if item_type == 'dynamic_text':
            return any(d.id == ref_id for d in self.state.dynamic_texts)
        if item_type == 'stream':
            return any(s.id == ref_id for s in self.state.streams)
        return False

    # Playback
    def _play(self):
        # Default behavior: play playlist loop
        if not self.state.playlist:
            QtWidgets.QMessageBox.warning(self, 'PLAY', 'Playlist je prázdný.')
            return
        # Play first item for skeleton
        self._play_playlist_index(0)

    def _play_playlist_index(self, ix: int):
        ix = ix % len(self.state.playlist)
        item = self.state.playlist[ix]
        if item.item_type in ('audiofile', 'spotify'):
            tr = next((t for t in self.state.tracks if t.id == item.ref_id), None)
            if tr and tr.source == 'audiofile' and tr.path:
                self._playlist_next_ix = ix + 1
                self.player.play_file(tr.path, label=f"{tr.title} — {tr.artist}")
                self.statusBar().showMessage(f'PLAY: {tr.title} — {tr.artist}', 3000)
            else:
                # Spotify playback requires a separate playback integration; skeleton skips.
                self._playlist_next_ix = ix + 1
                self._on_track_end()
        elif item.item_type == 'dynamic_text':
            # Dynamic text playback would synthesize via Azure and then play the wav.
            self._playlist_next_ix = ix + 1
            self._on_track_end()
        elif item.item_type == 'stream':
            st = next((s for s in self.state.streams if s.id == item.ref_id), None)
            if st:
                self._playlist_next_ix = ix + 1
                self.player.play_stream(st.url, label=f"Stream: {st.name}")

    def _stop(self):
        self.player.stop()

    def _mute(self, _=True):
        self.player.set_mute(not self.player.mute)

    def _boost(self, on: bool):
        self.player.set_boost(on)

    def _hotkey(self, ix: int):
        hk = self.state.hotkeys[ix]
        if not hk.item_type or not hk.ref_id:
            return
        # Interrupt current, play selected, then resume (skeleton: just play selected)
        if hk.item_type in ('audiofile', 'spotify'):
            tr = next((t for t in self.state.tracks if t.id == hk.ref_id), None)
            if tr and tr.source == 'audiofile' and tr.path:
                self.player.play_file(tr.path, label=f"HOTKEY: {tr.title}")
        elif hk.item_type == 'stream':
            st = next((s for s in self.state.streams if s.id == hk.ref_id), None)
            if st:
                self.player.play_stream(st.url, label=f"HOTKEY: {st.name}")

    def _on_track_end(self):
        # Continue playlist loop
        if getattr(self, '_playlist_next_ix', None) is None:
            return
        if not self.state.playlist:
            return
        self._play_playlist_index(self._playlist_next_ix)

    def _update_meters(self):
        m = self.player.meter
        self.footer.eye.set_state(
            rms=m.rms,
            peak=m.peak,
            muted=self.player.mute,
            stopped=not self.player.is_running,
            boost=self.player.boost,
        )

    def _on_settings_changed(self, d: dict):
        self.state.settings.spotify_api_key = d.get('spotify_api_key', '')
        self.state.settings.openai_api_key = d.get('openai_api_key', '')
        self.state.settings.azure_tts_key = d.get('azure_tts_key', '')
        self.state.settings.azure_tts_region = d.get('azure_tts_region', '')

    def closeEvent(self, e: QtGui.QCloseEvent) -> None:
        try:
            self.player.stop()
        except Exception:
            pass
        super().closeEvent(e)
