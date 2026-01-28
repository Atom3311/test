from aiogram.fsm.state import State, StatesGroup


class OnboardingStates(StatesGroup):
    awaiting_consent = State()
    awaiting_assessment = State()


class TherapyStates(StatesGroup):
    in_session = State()
