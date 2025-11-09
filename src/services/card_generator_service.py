from __future__ import annotations

import asyncio
from math import ceil
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

from PIL import Image, ImageDraw, ImageFont
import tqdm as tqdm_lib
from tqdm import tqdm

from utils.image_to_ascii import image_to_ascii


@dataclass(frozen=True)
class CardAnimationConfig:
    chars_per_frame: int = 3
    frame_duration_ms: int = 20
    cursor_blink_period: int = 6
    final_hold_seconds: float = 2.0
    max_render_workers: int = 8
    avatar_height: int = 30
    avatar_width: int = 60
    font_size: int = 22
    line_spacing: int = 4
    column_gap: int = 4
    font_paths: Sequence[str] = (
        "assets/fonts/JetBrainsMono-Regular.ttf",
        "consola.ttf",
        "Courier New.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    )
    palette_optimization: bool = False


@dataclass(frozen=True)
class StyledSegment:
    text: str
    color: str
    preserve_trailing: bool = False


@dataclass(frozen=True)
class Glyph:
    char: str
    color: Tuple[int, int, int]
    x: int
    y: int


class CardGeneratorService:
    def __init__(
        self,
        github_stats: dict,
        wakatime_stats: dict,
        theme: dict,
        animation_config: CardAnimationConfig | None = None,
    ) -> None:
        self.github_stats = github_stats or {}
        self.wakatime_stats = wakatime_stats or {}
        self.theme = theme or {}
        self.animation_config = animation_config or CardAnimationConfig()

        # Reasonable fallbacks in case theme colors are missing
        fallback = {
            "background": "#0A0A0A",
            "avatar": "#FF0883",
            "header": "#83FF08",
            "section_title": "#FF8308",
            "section_key": "#0883FF",
            "section_value": "#B4E1FD",
            "separator": "#08FF83",
            "cursor": "#B4E1FD",
        }

        self.color_scheme = {
            "background": self.theme.get("background", fallback["background"]),
            "avatar": self.theme.get("color_02", fallback["avatar"]),
            "header": self.theme.get("color_03", fallback["header"]),
            "section_title": self.theme.get("color_04", fallback["section_title"]),
            "section_key": self.theme.get("color_05", fallback["section_key"]),
            "section_value": self.theme.get("foreground", fallback["section_value"]),
            "separator": self.theme.get("color_07", fallback["separator"]),
            "cursor": self.theme.get("cursor", fallback["cursor"]),
        }

        self.card_width = 1080
        self.card_height = 700
        self.padding = 20
        self.font_size = self.animation_config.font_size
        self.char_width = 12
        self.char_height = 28
        self.line_height = self.char_height + self.animation_config.line_spacing

        self.colored_lines: List[List[StyledSegment]] = []
        self.char_stream: List[Tuple[str, str]] = []
        self.glyphs: List[Glyph] = []
        self.cursor_positions: List[Tuple[int, int]] = []
        self._color_cache: Dict[str, Tuple[int, int, int]] = {}
        self._font: ImageFont.FreeTypeFont | ImageFont.ImageFont | None = None

    @staticmethod
    def _log_stage(index: int, total: int, message: str) -> None:
        prefix = f"[{index}/{total}]"
        print(f"{prefix} {message}")

    def _log_info(self, message: str) -> None:
        writer = getattr(tqdm_lib, "write", None)
        if callable(writer):
            writer(message)
        else:
            print(message)

    async def generate_card(
        self,
        output_path: str | Path = "output/card.gif",
        animation_config: CardAnimationConfig | None = None,
    ) -> Path:
        config = animation_config or self.animation_config

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Ensure font metrics are available before building the card text
        self._prepare_font(config)

        total_stages = 4 + int(config.palette_optimization)
        stage_idx = 1

        self._log_stage(stage_idx, total_stages, "Building card data")
        card_text = self._generate_card_data(config)
        self._log_info(f"  characters: {len(card_text)}")

        stage_idx += 1
        self._log_stage(stage_idx, total_stages, "Preparing glyph layout")
        self._layout_characters(config)
        self._log_info(f"  glyphs: {len(self.glyphs)}")

        stage_idx += 1
        self._log_stage(stage_idx, total_stages, "Rendering frames")
        frames, durations = await self._generate_frames(config)

        if config.palette_optimization:
            stage_idx += 1
            self._log_stage(stage_idx, total_stages, "Optimizing palette")
            frames = self._optimize_palette(frames)

        stage_idx += 1
        self._log_stage(stage_idx, total_stages, f"Saving GIF ({len(frames)} frames)")
        self._save_gif(output_path, frames, durations)

        file_size_mb = output_path.stat().st_size / (1024 * 1024)
        self._log_info(f"✓ Card saved: {output_path} ({file_size_mb:.2f} MB)")

        return output_path

    def _generate_card_data(self, config: CardAnimationConfig) -> str:
        user_info = self.github_stats.get("user_info", {})
        repo_stats = self.github_stats.get("repository_stats", {})
        contrib_stats = self.github_stats.get("contribution_stats", {})
        weekly_stats = self.wakatime_stats.get("weekly_stats", {})
        all_time_stats = self.wakatime_stats.get("all_time_stats", {})

        self.colored_lines = []

        username = user_info.get("username")
        avatar_lines: List[str] = []

        if username:
            avatar_raw = image_to_ascii(
                f"https://github.com/{username}.png",
                height=config.avatar_height,
                width=config.avatar_width,
            )
            avatar_lines = avatar_raw.splitlines() if avatar_raw else []

        avatar_lines = [line.rstrip(" ") for line in avatar_lines]
        ascii_width = max((len(line) for line in avatar_lines), default=0)

        info_lines: List[List[StyledSegment]] = []

        name = user_info.get("name") or user_info.get("username") or "User"
        header = f"{name}@gl1tch-card"
        self._append_line([(header, self.color_scheme["header"])], info_lines)
        self._append_line(
            [(len(header) * "-", self.color_scheme["separator"])], info_lines
        )
        self._add_blank_line(info_lines)

        # About section
        self._add_section_header("About Me:", info_lines)
        self._add_kv_line(
            "Bio",
            user_info.get("bio") or "Full-stack developer passionate about open source",
            info_lines,
        )
        self._add_kv_line(
            "Location", user_info.get("location", "San Francisco, CA"), info_lines
        )
        self._add_kv_line("Followers", user_info.get("followers", 0), info_lines)
        self._add_kv_line("Following", user_info.get("following", 0), info_lines)
        self._add_blank_line(info_lines)

        # Work section (synthetic placeholders if missing)
        self._add_section_header("Work Information:", info_lines)
        self._add_kv_line(
            "Current Company", user_info.get("company", "Tech Corp Inc"), info_lines
        )
        self._add_kv_line(
            "Designation",
            user_info.get("designation", "Senior Software Engineer"),
            info_lines,
        )
        self._add_kv_line(
            "Current Experience", repo_stats.get("total_repos", 0), info_lines
        )
        self._add_kv_line(
            "Total Experience",
            repo_stats.get("public_repos", 0) + repo_stats.get("private_repos", 0),
            info_lines,
        )
        self._add_kv_line(
            "Achievements", "Led team of 8, Improved performance by 50%", info_lines
        )
        self._add_blank_line(info_lines)

        # Contact section
        self._add_section_header("Contact Information:", info_lines)
        if username:
            self._add_kv_line("GitHub", f"https://github.com/{username}", info_lines)
            self._add_kv_line("Twitter", f"@{username}", info_lines)
        self._add_blank_line(info_lines)

        # GitHub stats
        self._add_section_header("GitHub Stats:", info_lines)
        self._add_kv_line("Public Repos", repo_stats.get("public_repos", 0), info_lines)
        self._add_kv_line(
            "Private Repos", repo_stats.get("private_repos", 0), info_lines
        )
        self._add_kv_line("Total Stars", repo_stats.get("total_stars", 0), info_lines)
        self._add_kv_line("Total Forks", repo_stats.get("total_forks", 0), info_lines)
        self._add_kv_line(
            "Commits", contrib_stats.get("total_commit_contributions", 0), info_lines
        )
        top_languages = repo_stats.get("languages", {})
        if top_languages:
            lang_str = ", ".join(
                f"{lang} ({count})" for lang, count in list(top_languages.items())[:5]
            )
            self._add_kv_line("Languages", lang_str, info_lines)
        if repo_stats.get("most_starred_repo"):
            repo = repo_stats["most_starred_repo"]
            self._add_kv_line(
                "Top Repo",
                f"{repo.get('name', 'N/A')} ({repo.get('stargazerCount', 0)}★)",
                info_lines,
            )
        self._add_blank_line(info_lines)

        # WakaTime stats
        self._add_section_header("Time Distribution:", info_lines)
        self._add_kv_line("Timezone", weekly_stats.get("timezone", "UTC"), info_lines)
        self._add_kv_line(
            "Weekly Total", weekly_stats.get("total_coding_time_text", "--"), info_lines
        )
        self._add_kv_line(
            "Daily Average",
            weekly_stats.get("daily_average_time_text")
            or weekly_stats.get("daily_average_time", "--"),
            info_lines,
        )
        self._add_kv_line(
            "All-time",
            all_time_stats.get("all_time_stats", {}).get("text", "--"),
            info_lines,
        )
        editors = weekly_stats.get("editor") or weekly_stats.get("editors")
        if editors:
            self._add_kv_line("Editor", editors, info_lines)
        languages = weekly_stats.get("language_usage", [])
        if languages:
            language_line = ", ".join(
                f"{lang.get('language_name')} ({lang.get('time_spent_text')})"
                for lang in languages[:5]
            )
            self._add_kv_line("Top Languages", language_line, info_lines)
        projects = weekly_stats.get("most_active_projects", [])
        if projects:
            project_line = ", ".join(proj.get("project_name") for proj in projects[:5])
            self._add_kv_line("Projects", project_line, info_lines)

        ascii_gap = " " * self.animation_config.column_gap
        total_rows = max(len(avatar_lines), len(info_lines))
        for row_index in range(total_rows):
            line_segments: List[StyledSegment] = []

            if ascii_width > 0:
                ascii_text = (
                    avatar_lines[row_index] if row_index < len(avatar_lines) else ""
                )
                if ascii_text:
                    line_segments.append(
                        StyledSegment(ascii_text, self.color_scheme["avatar"])
                    )
                padding = ascii_width - len(ascii_text)
                if padding > 0:
                    line_segments.append(
                        StyledSegment(
                            " " * padding,
                            self.color_scheme["section_value"],
                            preserve_trailing=True,
                        )
                    )
                if self.animation_config.column_gap > 0:
                    line_segments.append(
                        StyledSegment(
                            ascii_gap,
                            self.color_scheme["section_value"],
                            preserve_trailing=True,
                        )
                    )

            if row_index < len(info_lines):
                line_segments.extend(info_lines[row_index])

            self.colored_lines.append(line_segments)

        self.char_stream = []
        for line in self.colored_lines:
            for segment in line:
                if not segment.text:
                    continue
                text = (
                    segment.text
                    if segment.preserve_trailing
                    else segment.text.rstrip(" ")
                )
                if not text:
                    continue
                for char in text:
                    self.char_stream.append((char, segment.color))
            self.char_stream.append(("\n", self.color_scheme["section_value"]))

        return "".join(char for char, _ in self.char_stream)

    def _add_line(self, segments: Iterable[Tuple[str, str]]) -> None:
        self._append_line(segments, self.colored_lines)

    def _append_line(
        self,
        segments: Iterable[Tuple[str, str] | Tuple[str, str, bool]],
        target: List[List[StyledSegment]],
    ) -> None:
        line_segments: List[StyledSegment] = []
        for segment in segments:
            if len(segment) == 2:
                text, color = segment  # type: ignore[misc]
                preserve = False
            else:
                text, color, preserve = segment  # type: ignore[misc]
            line_segments.append(
                StyledSegment(text=text, color=color, preserve_trailing=preserve)
            )
        target.append(line_segments)

    def _add_blank_line(self, target: List[List[StyledSegment]] | None = None) -> None:
        destination = target or self.colored_lines
        self._append_line([("", self.color_scheme["section_value"])], destination)

    def _add_section_header(
        self, title: str, target: List[List[StyledSegment]] | None = None
    ) -> None:
        destination = target or self.colored_lines
        self._append_line([(title, self.color_scheme["section_title"])], destination)
        self._append_line([("---", self.color_scheme["separator"])], destination)

    def _add_kv_line(
        self, key: str, value: object, target: List[List[StyledSegment]] | None = None
    ) -> None:
        destination = target or self.colored_lines
        text_value = "N/A" if value is None else str(value)
        self._append_line(
            [
                (f"{key}: ", self.color_scheme["section_key"]),
                (text_value, self.color_scheme["section_value"]),
            ],
            destination,
        )

    async def _generate_frames(
        self, config: CardAnimationConfig
    ) -> Tuple[List[Image.Image], List[int]]:
        return await asyncio.to_thread(self._render_frames_sync, config)

    def _optimize_palette(self, frames: List[Image.Image]) -> List[Image.Image]:
        return [
            frame.convert("P", palette=Image.ADAPTIVE)
            for frame in tqdm(
                frames,
                desc="Quantizing palette",
                unit="frame",
                leave=False,
            )
        ]

    def _save_gif(
        self,
        output_path: Path,
        frames: List[Image.Image],
        durations: List[int],
    ) -> None:
        if not frames:
            raise ValueError("No frames to save.")

        frames[0].save(
            output_path,
            save_all=True,
            append_images=frames[1:],
            duration=durations,
            loop=0,
            optimize=True,
            disposal=2,
        )

    def _prepare_font(self, config: CardAnimationConfig) -> None:
        if self._font is not None:
            return

        for font_path in config.font_paths:
            try:
                self._font = ImageFont.truetype(str(font_path), config.font_size)
                break
            except OSError:
                continue

        if self._font is None:
            self._font = ImageFont.load_default()

        bbox = self._font.getbbox("M")
        self.char_width = max(1, bbox[2] - bbox[0])
        self.char_height = max(1, bbox[3] - bbox[1])
        self.line_height = self.char_height + config.line_spacing

    def _render_frames_sync(
        self, config: CardAnimationConfig
    ) -> Tuple[List[Image.Image], List[int]]:
        if not self.glyphs or not self.cursor_positions:
            raise ValueError("Glyph layout not prepared before frame rendering.")

        total_chars = len(self.glyphs)
        step = max(1, config.chars_per_frame)

        bg_color = self._hex_to_rgb(self.color_scheme["background"])
        cursor_color = self._hex_to_rgb(self.color_scheme["cursor"])

        base_image = Image.new("RGB", (self.card_width, self.card_height), bg_color)
        base_draw = ImageDraw.Draw(base_image)

        frames: List[Image.Image] = []
        durations: List[int] = []

        frame_index = 0

        total_steps = 1 + ceil(total_chars / step)
        final_hold_frames = max(
            1,
            int(round((config.final_hold_seconds * 1000) / config.frame_duration_ms)),
        )
        total_frames = total_steps + final_hold_frames

        progress = tqdm(
            total=total_frames,
            desc="Rendering frames",
            unit="frame",
            leave=False,
        )

        def add_frame(cursor_idx: int) -> None:
            nonlocal frame_index
            frame = base_image.copy()
            if self._should_show_cursor(frame_index, config):
                cursor_x, cursor_y = self.cursor_positions[cursor_idx]
                ImageDraw.Draw(frame).rectangle(
                    [
                        cursor_x,
                        cursor_y,
                        cursor_x + self.char_width,
                        cursor_y + self.char_height,
                    ],
                    fill=cursor_color,
                )
            frames.append(frame)
            durations.append(config.frame_duration_ms)
            frame_index += 1
            progress.update(1)

        add_frame(0)

        typed = 0
        while typed < total_chars:
            typed_next = min(total_chars, typed + step)
            for glyph in self.glyphs[typed:typed_next]:
                if glyph.char == "\n":
                    continue
                base_draw.text(
                    (glyph.x, glyph.y), glyph.char, fill=glyph.color, font=self._font
                )
            typed = typed_next
            add_frame(typed)

        last_cursor_idx = len(self.cursor_positions) - 1
        for _ in range(final_hold_frames):
            add_frame(last_cursor_idx)

        progress.close()

        return frames, durations

    def _layout_characters(self, config: CardAnimationConfig) -> None:
        self.glyphs = []
        self.cursor_positions = []

        x = self.padding
        y = self.padding
        self.cursor_positions.append((x, y))

        for char, color_hex in self.char_stream:
            if char == "\n":
                self.glyphs.append(
                    Glyph(char=char, color=self._hex_to_rgb(color_hex), x=x, y=y)
                )
                x = self.padding
                y += self.line_height
                self.cursor_positions.append((x, y))
                continue

            color_rgb = self._hex_to_rgb(color_hex)
            self.glyphs.append(Glyph(char=char, color=color_rgb, x=x, y=y))
            x += self._glyph_advance(char)
            self.cursor_positions.append((x, y))

        if not self.cursor_positions:
            self.cursor_positions.append((self.padding, self.padding))

    def _glyph_advance(self, char: str) -> int:
        if self._font is None:
            return self.char_width

        bbox = self._font.getbbox(char)
        if not bbox:
            return self.char_width

        advance = bbox[2] - bbox[0]
        return advance if advance > 0 else self.char_width

    def _should_show_cursor(
        self, frame_index: int, config: CardAnimationConfig
    ) -> bool:
        period = max(1, config.cursor_blink_period)
        return (frame_index % period) < (period // 2 or 1)

    @staticmethod
    def _normalize_hex(hex_color: str) -> str:
        if not hex_color:
            return "000000"
        cleaned = hex_color.strip().lstrip("#")
        if len(cleaned) == 3:
            cleaned = "".join(c * 2 for c in cleaned)
        return cleaned.lower()

    def _hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        normalized = self._normalize_hex(hex_color)
        if normalized not in self._color_cache:
            self._color_cache[normalized] = tuple(
                int(normalized[i : i + 2], 16) for i in (0, 2, 4)
            )
        return self._color_cache[normalized]
