from __future__ import annotations
from dataclasses import dataclass
from aiogram import Bot
from .config import Settings
from .infra.db import connect, ensure_schema
from .infra.repos.polls import PollsRepo
from .infra.repos.votes import VotesRepo
from .infra.repos.teachers import TeachersRepo
from .infra.repos.settings import SettingsRepo
from .services.payroll import PayrollService
from .services.polls import PollsService


@dataclass
class AppContext:
    bot: Bot
    settings: Settings
    polls: PollsRepo
    votes: VotesRepo
    teachers: TeachersRepo
    conf: SettingsRepo
    payroll_service: PayrollService
    polls_service: PollsService

    @classmethod
    def build(cls, bot: Bot, settings: Settings) -> "AppContext":
        ensure_schema(str(settings.database_file), connect)
        polls = PollsRepo(str(settings.database_file), connect)
        votes = VotesRepo(str(settings.database_file), connect)
        teachers = TeachersRepo(str(settings.database_file), connect)
        conf = SettingsRepo(str(settings.database_file), connect)
        payroll = PayrollService(teachers=teachers, votes=votes)
        polls_service = PollsService(bot=bot, polls=polls, conf=conf)
        return cls(
            bot=bot,
            settings=settings,
            polls=polls,
            votes=votes,
            teachers=teachers,
            conf=conf,
            payroll_service=payroll,
            polls_service=polls_service,
        )
