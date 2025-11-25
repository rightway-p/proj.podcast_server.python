from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Optional

import httpx
from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal
from textual.message import Message
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.validation import Length
from textual.widgets import (
    Button,
    Checkbox,
    Footer,
    Header,
    Input,
    Label,
    RichLog,
    Static,
    Tree,
)


from ..client import (
    AutomationServiceClient,
    Channel,
    PipelineChannel,
    PipelineConfiguration,
    PipelinePlaylist,
    Playlist,
    Schedule,
)


class ChannelSubmitted(Message):
    def __init__(
        self,
        *,
        form: ModalScreen,
        slug: str,
        title: str,
        description: Optional[str],
        channel_id: Optional[int],
    ) -> None:
        super().__init__()
        self.form = form
        self.slug = slug
        self.title = title
        self.description = description
        self.channel_id = channel_id


class PlaylistSubmitted(Message):
    def __init__(
        self,
        *,
        form: ModalScreen,
        channel_id: int,
        playlist_id: Optional[int],
        youtube_playlist_id: str,
        title: Optional[str],
        is_active: bool,
    ) -> None:
        super().__init__()
        self.form = form
        self.channel_id = channel_id
        self.playlist_id = playlist_id
        self.youtube_playlist_id = youtube_playlist_id
        self.title = title
        self.is_active = is_active


class ScheduleSubmitted(Message):
    def __init__(
        self,
        *,
        form: ModalScreen,
        playlist_id: int,
        schedule_id: Optional[int],
        days_of_week: list[str],
        run_time: str,
        timezone: str,
        is_active: bool,
        next_run_at: Optional[str],
    ) -> None:
        super().__init__()
        self.form = form
        self.playlist_id = playlist_id
        self.schedule_id = schedule_id
        self.days_of_week = days_of_week
        self.run_time = run_time
        self.timezone = timezone
        self.is_active = is_active
        self.next_run_at = next_run_at


@dataclass
class TreeData:
    type: str
    channel: Optional[Channel] = None
    playlist: Optional[Playlist] = None
    schedule: Optional[Schedule] = None


class ChannelForm(ModalScreen[dict[str, Any] | None]):
    def __init__(self, *, channel: Channel | None = None) -> None:
        super().__init__()
        self.channel = channel

    def compose(self) -> ComposeResult:
        title = "채널 수정" if self.channel else "채널 추가"
        yield Container(
            Label(title, id="form-title"),
            Input(
                placeholder="slug",
                value=self.channel.slug if self.channel else "",
                id="slug",
                disabled=self.channel is not None,
                validators=[Length(minimum=1)],
            ),
            Input(
                placeholder="title",
                value=self.channel.title if self.channel else "",
                id="title",
                validators=[Length(minimum=1)],
            ),
            Input(
                placeholder="description",
                value=self.channel.description or "" if self.channel else "",
                id="description",
            ),
            Horizontal(
                Button("취소", id="cancel"),
                Button("저장", id="save", variant="primary"),
                id="form-buttons",
            ),
            id="form-container",
        )

    @on(Button.Pressed, "#cancel")
    def cancel(self) -> None:
        self.dismiss(None)

    @on(Button.Pressed, "#save")
    def save(self) -> None:
        slug = self.query_one("#slug", Input).value.strip()
        title = self.query_one("#title", Input).value.strip()
        description = self.query_one("#description", Input).value.strip() or None
        self.app.post_message(
            ChannelSubmitted(
                form=self,
                slug=slug,
                title=title,
                description=description,
                channel_id=self.channel.id if self.channel else None,
            )
        )
        self.dismiss(None)


class PlaylistForm(ModalScreen[dict[str, Any] | None]):
    def __init__(
        self,
        *,
        channel: Channel,
        playlist: Playlist | None = None,
    ) -> None:
        super().__init__()
        self.channel = channel
        self.playlist = playlist

    def compose(self) -> ComposeResult:
        title = "플레이리스트 수정" if self.playlist else "플레이리스트 추가"
        yield Container(
            Label(title, id="form-title"),
            Label(f"채널: {self.channel.title}", id="form-subtitle"),
            Input(
                placeholder="YouTube playlist ID",
                value=self.playlist.youtube_playlist_id if self.playlist else "",
                id="playlist_id",
                disabled=self.playlist is not None,
                validators=[Length(minimum=3)],
            ),
            Input(
                placeholder="title",
                value=self.playlist.title if self.playlist else "",
                id="title",
            ),
            Checkbox(
                "활성화", id="is_active", value=self.playlist.is_active if self.playlist else True
            ),
            Horizontal(
                Button("취소", id="cancel"),
                Button("저장", id="save", variant="primary"),
                id="form-buttons",
            ),
            id="form-container",
        )

    @on(Button.Pressed, "#cancel")
    def cancel(self) -> None:
        self.dismiss(None)

    @on(Button.Pressed, "#save")
    def save(self) -> None:
        youtube_playlist_id = self.query_one("#playlist_id", Input).value.strip()
        title = self.query_one("#title", Input).value.strip() or None
        is_active = self.query_one("#is_active", Checkbox).value
        self.app.post_message(
            PlaylistSubmitted(
                form=self,
                channel_id=self.channel.id,
                playlist_id=self.playlist.id if self.playlist else None,
                youtube_playlist_id=youtube_playlist_id,
                title=title,
                is_active=is_active,
            )
        )
        self.dismiss(None)


class ScheduleForm(ModalScreen[dict[str, Any] | None]):
    def __init__(
        self,
        *,
        playlist: Playlist,
        schedule: Schedule | None = None,
    ) -> None:
        super().__init__()
        self.playlist = playlist
        self.schedule = schedule

    def compose(self) -> ComposeResult:
        title = "스케줄 수정" if self.schedule else "스케줄 추가"
        yield Container(
            Label(title, id="form-title"),
            Label(f"플레이리스트: {self.playlist.title or self.playlist.youtube_playlist_id}", id="form-subtitle"),
            Input(
                placeholder="요일 (예: mon,tue,wed)",
                value=",".join(self.schedule.days_of_week) if self.schedule else "mon,tue,wed,thu,fri",
                id="days",
                validators=[Length(minimum=3)],
            ),
            Input(
                placeholder="실행 시각 (HH:MM)",
                value=self.schedule.run_time if self.schedule else "07:00",
                id="run_time",
                validators=[Length(minimum=4)],
            ),
            Input(
                placeholder="timezone",
                value=self.schedule.timezone if self.schedule else "Asia/Seoul",
                id="timezone",
            ),
            Checkbox(
                "활성화",
                id="is_active",
                value=self.schedule.is_active if self.schedule else True,
            ),
            Input(
                placeholder="next run (ISO8601, optional)",
                value=(
                    self.schedule.next_run_at.isoformat()
                    if self.schedule and self.schedule.next_run_at
                    else ""
                ),
                id="next_run",
            ),
            Horizontal(
                Button("취소", id="cancel"),
                Button("저장", id="save", variant="primary"),
                id="form-buttons",
            ),
            id="form-container",
        )

    @on(Button.Pressed, "#cancel")
    def cancel(self) -> None:
        self.dismiss(None)

    @on(Button.Pressed, "#save")
    def save(self) -> None:
        days_value = self.query_one("#days", Input).value.strip()
        run_time = self.query_one("#run_time", Input).value.strip()
        timezone = self.query_one("#timezone", Input).value.strip() or "Asia/Seoul"
        is_active = self.query_one("#is_active", Checkbox).value
        next_run_value = self.query_one("#next_run", Input).value.strip() or None
        days_of_week = [day.strip() for day in days_value.split(",") if day.strip()]
        if not days_of_week:
            days_of_week = ["mon"]
        self.app.post_message(
            ScheduleSubmitted(
                form=self,
                playlist_id=self.playlist.id,
                schedule_id=self.schedule.id if self.schedule else None,
                days_of_week=days_of_week,
                run_time=run_time or "07:00",
                timezone=timezone,
                is_active=is_active,
                next_run_at=next_run_value,
            )
        )
        self.dismiss(None)


class PipelineApp(App[None]):
    CSS = """
    #layout {
        height: 100%;
    }
    #tree-container {
        width: 60%;
    }
    #info-panel {
        width: 40%;
        padding: 1;
    }
    #log {
        height: 10;
    }
    #form-container {
        padding: 1 2;
        width: 60;
        border: round $primary;
    }
    #form-buttons {
        layout: horizontal;
        padding-top: 1;
        padding-left: 1;
        padding-right: 1;
    }
    #form-buttons Button {
        margin-right: 1;
    }
    #form-title {
        padding-bottom: 1;
    }
    #form-subtitle {
        padding-bottom: 1;
        color: $text-muted;
    }
    """

    BINDINGS = [
        Binding("ctrl+r", "refresh", "새로고침", priority=True),
        Binding("ctrl+a", "add_channel", "채널 추가", priority=True),
        Binding("ctrl+e", "edit_item", "수정", priority=True),
        Binding("ctrl+p", "add_playlist", "플리 추가", priority=True),
        Binding("ctrl+s", "add_schedule", "스케줄 추가", priority=True),
        Binding("ctrl+x", "delete_item", "삭제", priority=True),
        Binding("ctrl+t", "manual_trigger", "즉시 실행", priority=True),
        Binding("ctrl+q", "quit", "종료", priority=True),
    ]

    config: reactive[PipelineConfiguration | None] = reactive(None)

    def __init__(self) -> None:
        super().__init__()
        self.client: AutomationServiceClient | None = None

    async def on_mount(self) -> None:
        self.client = AutomationServiceClient()
        await self.action_refresh()

    async def on_unmount(self) -> None:
        if self.client is not None:
            await self.client.close()

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="layout"):
            tree = Tree("채널", id="channel-tree", data=TreeData(type="root"))
            tree.show_root = False
            yield Container(tree, id="tree-container")
            with Container(id="info-panel"):
                yield Static("선택된 항목 정보", id="info-title")
                self.info_log = RichLog(id="info-log", highlight=False, wrap=True)
                yield self.info_log
        self.log_widget = RichLog(id="log", highlight=True, wrap=True)
        yield self.log_widget
        yield Footer()

    def log_info(self, message: str) -> None:
        if hasattr(self, "log_widget"):
            self.log_widget.write(message)

    def update_info_panel(self, data: TreeData | None) -> None:
        if not hasattr(self, "info_log"):
            return
        info = self.info_log
        info.clear()
        if data is None:
            return
        if data.type == "channel" and data.channel:
            channel = data.channel
            info.write(f"채널: {channel.title} ({channel.slug})")
            info.write(channel.description or "설명 없음")
        elif data.type == "playlist" and data.playlist:
            playlist = data.playlist
            info.write(f"플레이리스트: {playlist.title or playlist.youtube_playlist_id}")
            info.write(f"활성화: {'예' if playlist.is_active else '아니오'}")
        elif data.type == "schedule" and data.schedule:
            schedule = data.schedule
            days = "/".join(schedule.days_of_week)
            info.write(f"스케줄: {days} {schedule.run_time} ({schedule.timezone})")
            info.write(f"타임존: {schedule.timezone}")
            if schedule.next_run_at:
                info.write(f"다음 실행: {schedule.next_run_at}")

    async def action_refresh(self) -> None:
        tree = self.query_one("#channel-tree", Tree)
        if tree.root is not None:
            for child in list(tree.root.children):
                child.remove()
        self.update_info_panel(None)
        if self.client is None:
            return
        try:
            config = await self.client.fetch_configuration()
        except httpx.HTTPError as exc:
            self.log_info(f"[red]API 호출 실패:[/red] {exc}")
            return
        self.config = config
        for channel_entry in config.channels:
            self._add_channel_node(tree, channel_entry)
        tree.root.expand_all()
        self.log_info("구성이 새로고침되었습니다.")

    def _add_channel_node(self, tree: Tree, channel_entry: PipelineChannel) -> None:
        channel = channel_entry.channel
        channel_node = tree.root.add(
            f"[b]{channel.title}[/b] ({channel.slug})",
            data=TreeData(type="channel", channel=channel),
        )
        for playlist_entry in channel_entry.playlists:
            playlist = playlist_entry.playlist
            status = "✅" if playlist.is_active else "🚫"
            playlist_label = f"{status} {playlist.title or playlist.youtube_playlist_id}"
            playlist_node = channel_node.add(
                playlist_label,
                data=TreeData(
                    type="playlist",
                    channel=channel,
                    playlist=playlist,
                ),
            )
            for schedule in playlist_entry.schedules:
                schedule_label = (
                    f"⏱ {'/'.join(schedule.days_of_week)} {schedule.run_time} ({schedule.timezone})"
                )
                playlist_node.add(
                    schedule_label,
                    data=TreeData(
                        type="schedule",
                        channel=channel,
                        playlist=playlist,
                        schedule=schedule,
                    ),
                )

    def get_selected_data(self) -> TreeData | None:
        tree = self.query_one("#channel-tree", Tree)
        if tree.cursor_node is None:
            return None
        return tree.cursor_node.data

    @on(Tree.NodeSelected, "#channel-tree")
    def show_selected_info(self, event: Tree.NodeSelected) -> None:
        data: TreeData | None = event.node.data
        self.update_info_panel(data)

    async def action_add_channel(self) -> None:
        self.push_screen(ChannelForm())

    async def action_edit_item(self) -> None:
        data = self.get_selected_data()
        if not data or self.client is None:
            return
        if data.type == "channel" and data.channel:
            self.push_screen(ChannelForm(channel=data.channel))
        elif data.type == "playlist" and data.playlist and data.channel:
            self.push_screen(PlaylistForm(channel=data.channel, playlist=data.playlist))
        elif data.type == "schedule" and data.schedule and data.playlist:
            self.push_screen(ScheduleForm(playlist=data.playlist, schedule=data.schedule))

    async def action_add_playlist(self) -> None:
        data = self.get_selected_data()
        if not data:
            self.log_info("플레이리스트를 추가할 채널을 선택하세요.")
            return
        channel = data.channel if data.type != "channel" else data.channel
        if channel is None:
            self.log_info("채널을 선택하세요.")
            return
        self.push_screen(PlaylistForm(channel=channel))

    async def action_add_schedule(self) -> None:
        data = self.get_selected_data()
        playlist = data.playlist if data else None
        if data and data.type == "schedule":
            playlist = data.playlist
        if playlist is None:
            self.log_info("스케줄을 추가하려면 플레이리스트를 선택하세요.")
            return
        self.push_screen(ScheduleForm(playlist=playlist))

    async def action_delete_item(self) -> None:
        data = self.get_selected_data()
        if not data or self.client is None:
            return
        try:
            if data.type == "channel" and data.channel:
                await self.client.delete_channel(data.channel.id)
                self.log_info("채널이 삭제되었습니다.")
            elif data.type == "playlist" and data.playlist:
                await self.client.delete_playlist(data.playlist.id)
                self.log_info("플레이리스트가 삭제되었습니다.")
            elif data.type == "schedule" and data.schedule:
                await self.client.delete_schedule(data.schedule.id)
                self.log_info("스케줄이 삭제되었습니다.")
            else:
                self.log_info("삭제할 항목을 선택하세요.")
                return
            await self.action_refresh()
        except httpx.HTTPError as exc:
            self.log_info(f"[red]삭제 실패:[/red] {exc}")

    async def action_manual_trigger(self) -> None:
        now = datetime.now(UTC).isoformat()
        self.log_info(
            f"[yellow]즉시 실행 요청[/yellow] — 크론 외 실행은 아직 구현되지 않았습니다. ({now})"
        )

    @on(ChannelSubmitted)
    async def handle_channel_submitted(self, event: ChannelSubmitted) -> None:
        if self.client is None:
            return
        try:
            if event.channel_id is None:
                await self.client.create_channel(
                    slug=event.slug,
                    title=event.title,
                    description=event.description,
                )
                self.log_info("채널이 추가되었습니다.")
            else:
                await self.client.update_channel(
                    event.channel_id,
                    title=event.title,
                    description=event.description,
                )
                self.log_info("채널이 수정되었습니다.")
            await self.action_refresh()
        except httpx.HTTPError as exc:
            self.log_info(f"[red]API 오류:[/red] {exc}")

    @on(PlaylistSubmitted)
    async def handle_playlist_submitted(self, event: PlaylistSubmitted) -> None:
        if self.client is None:
            return
        try:
            if event.playlist_id is None:
                await self.client.create_playlist(
                    channel_id=event.channel_id,
                    youtube_playlist_id=event.youtube_playlist_id,
                    title=event.title,
                    is_active=event.is_active,
                )
                self.log_info("플레이리스트가 추가되었습니다.")
            else:
                await self.client.update_playlist(
                    event.playlist_id,
                    title=event.title,
                    is_active=event.is_active,
                )
                self.log_info("플레이리스트가 수정되었습니다.")
            await self.action_refresh()
        except httpx.HTTPError as exc:
            self.log_info(f"[red]API 오류:[/red] {exc}")

    @on(ScheduleSubmitted)
    async def handle_schedule_submitted(self, event: ScheduleSubmitted) -> None:
        if self.client is None:
            return
        try:
            if event.schedule_id is None:
                await self.client.create_schedule(
                    playlist_id=event.playlist_id,
                    days_of_week=event.days_of_week,
                    run_time=event.run_time,
                    timezone=event.timezone,
                    is_active=event.is_active,
                    next_run_at=event.next_run_at,
                )
                self.log_info("스케줄이 추가되었습니다.")
            else:
                await self.client.update_schedule(
                    event.schedule_id,
                    days_of_week=event.days_of_week,
                    run_time=event.run_time,
                    timezone=event.timezone,
                    is_active=event.is_active,
                    next_run_at=event.next_run_at,
                )
                self.log_info("스케줄이 수정되었습니다.")
            await self.action_refresh()
        except httpx.HTTPError as exc:
            self.log_info(f"[red]API 오류:[/red] {exc}")


def run() -> None:
    PipelineApp().run()


if __name__ == "__main__":
    run()
