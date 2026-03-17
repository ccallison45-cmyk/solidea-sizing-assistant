"""Per-product conversation flow definitions.

Each flow declares the questions to ask, in order, with owner-voice text.
Placeholder text will be replaced with real owner Q&A patterns in Phase 2.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class MeasurementQuestion:
    """One question in a conversation flow."""

    id: str
    measurement_key: str
    text: str
    help_text: str
    dont_know_response: str
    accept_formats: list[str]
    input_type: str  # "height", "weight", "circumference"
    required: bool = True
    condition: str | None = None  # None=always, "between_sizes"=only if ambiguous
    skip_allowed: bool = False
    tips: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ConversationFlow:
    """Complete conversation flow for a product type."""

    product_type: str
    display_name: str
    greeting: str
    questions: list[MeasurementQuestion]
    between_sizes_advice: str
    result_template: str
    out_of_range_template: str
    contact_fallback: str = (
        "If you're unsure, please email info@solideaus.com or call 888-841-8834 "
        "and we'll help you find the perfect fit!"
    )


# ── Shared question builders ────────────────────────────────────
# These reduce repetition across the 20 product types.


def _height_question(required: bool = True, condition: str | None = None) -> MeasurementQuestion:
    return MeasurementQuestion(
        id="height",
        measurement_key="height_cm",
        text="What's your height?",
        help_text="You can tell me in feet/inches (like 5'7\") or centimeters.",
        dont_know_response="No worries! A rough estimate is fine — for example, are you closer to 5'2\", 5'5\", or 5'8\"?",
        accept_formats=["cm", "feet_inches"],
        input_type="height",
        required=required,
        condition=condition,
        skip_allowed=not required,
        tips=["If you're 5'1\" or under, capris may fit better than full-length leggings."],
    )


def _weight_question(required: bool = True, condition: str | None = None) -> MeasurementQuestion:
    return MeasurementQuestion(
        id="weight",
        measurement_key="weight_kg",
        text="And your weight?",
        help_text="In pounds or kilograms — either works!",
        dont_know_response="A rough estimate is perfectly fine. It helps me narrow down between sizes.",
        accept_formats=["kg", "lbs"],
        input_type="weight",
        required=required,
        condition=condition,
        skip_allowed=not required,
    )


def _hip_question(required: bool = True, condition: str | None = None) -> MeasurementQuestion:
    return MeasurementQuestion(
        id="hip",
        measurement_key="hip_circumference_cm",
        text="Do you know your hip measurement?",
        help_text="Measure around the widest part of your hips/buttocks with a soft tape measure.",
        dont_know_response="That's okay! Your height and weight usually get us close enough.",
        accept_formats=["cm", "inches"],
        input_type="circumference",
        required=required,
        condition=condition,
        skip_allowed=not required,
    )


def _waist_question(required: bool = True, condition: str | None = None) -> MeasurementQuestion:
    return MeasurementQuestion(
        id="waist",
        measurement_key="waist_circumference_cm",
        text="And your waist measurement?",
        help_text="Measure around your natural waist — the narrowest part of your torso, usually just above the belly button.",
        dont_know_response="No problem! We can work with your other measurements.",
        accept_formats=["cm", "inches"],
        input_type="circumference",
        required=required,
        condition=condition,
        skip_allowed=not required,
    )


def _bust_question() -> MeasurementQuestion:
    return MeasurementQuestion(
        id="bust",
        measurement_key="bust_circumference_cm",
        text="What's your bust measurement?",
        help_text="Measure around the fullest part of your bust with a soft tape measure, keeping the tape level.",
        dont_know_response="You can use your bra size as a guide! For example, a 36C bust is roughly 38-39 inches around.",
        accept_formats=["cm", "inches"],
        input_type="circumference",
    )


def _underbust_question() -> MeasurementQuestion:
    return MeasurementQuestion(
        id="underbust",
        measurement_key="underbust_circumference_cm",
        text="And your underbust measurement?",
        help_text="Measure just below your bust, right under the breast tissue, snug but comfortable.",
        dont_know_response="Your bra band size is close to your underbust — for example, a 34 band is about 34 inches.",
        accept_formats=["cm", "inches"],
        input_type="circumference",
    )


def _upper_arm_question() -> MeasurementQuestion:
    return MeasurementQuestion(
        id="upper_arm",
        measurement_key="upper_arm_circumference_cm",
        text="What's your upper arm (bicep) circumference?",
        help_text="Measure around the widest part of your upper arm, about halfway between shoulder and elbow.",
        dont_know_response="You can wrap a string around your upper arm and measure the string with a ruler!",
        accept_formats=["cm", "inches"],
        input_type="circumference",
    )


def _forearm_question() -> MeasurementQuestion:
    return MeasurementQuestion(
        id="forearm",
        measurement_key="forearm_circumference_cm",
        text="And your forearm circumference?",
        help_text="Measure around the widest part of your forearm, a couple inches below the elbow.",
        dont_know_response="Try wrapping a flexible tape or string around your forearm at its widest point.",
        accept_formats=["cm", "inches"],
        input_type="circumference",
    )


def _wrist_question() -> MeasurementQuestion:
    return MeasurementQuestion(
        id="wrist",
        measurement_key="wrist_circumference_cm",
        text="And your wrist circumference?",
        help_text="Measure around your wrist bone — where you'd wear a watch.",
        dont_know_response="Most women's wrists are 5.5-7 inches. Does that range sound about right for you?",
        accept_formats=["cm", "inches"],
        input_type="circumference",
    )


def _calf_question() -> MeasurementQuestion:
    return MeasurementQuestion(
        id="calf",
        measurement_key="calf_circumference_cm",
        text="What's your calf circumference?",
        help_text="Measure around the widest part of your calf muscle.",
        dont_know_response="Sit down and wrap a tape measure around the thickest part of your calf.",
        accept_formats=["cm", "inches"],
        input_type="circumference",
    )


def _ankle_question() -> MeasurementQuestion:
    return MeasurementQuestion(
        id="ankle",
        measurement_key="ankle_circumference_cm",
        text="And your ankle circumference?",
        help_text="Measure around the narrowest part of your ankle, just above the ankle bone.",
        dont_know_response="Most ankle circumferences are between 7-11 inches. Can you estimate yours?",
        accept_formats=["cm", "inches"],
        input_type="circumference",
    )


# ── Default templates ────────────────────────────────────────────

_DEFAULT_BETWEEN = (
    "You're between sizes {size1} and {size2}. "
    "If you prefer a snugger, more therapeutic compression feel, go with {size1}. "
    "If you prefer a more comfortable, everyday fit, go with {size2}."
)

_DEFAULT_RESULT = "Based on your measurements, I recommend a **{size}**!"

_DEFAULT_OOR = (
    "Your measurements fall outside our standard size range. "
    "The closest size would be {size}, but I'd recommend reaching out to us "
    "for personalized help."
)


# ── Flow definitions ─────────────────────────────────────────────

FLOWS: dict[str, ConversationFlow] = {}


def _register(flow: ConversationFlow) -> None:
    FLOWS[flow.product_type] = flow


# --- Lower body (height + weight based) ---

_register(
    ConversationFlow(
        product_type="leggings",
        display_name="Leggings",
        greeting="Let's find your perfect legging size! I'll ask a few quick questions.",
        questions=[
            _height_question(),
            _weight_question(),
            _hip_question(required=False, condition="between_sizes"),
            _waist_question(required=False, condition="between_sizes"),
        ],
        between_sizes_advice=_DEFAULT_BETWEEN,
        result_template=_DEFAULT_RESULT,
        out_of_range_template=_DEFAULT_OOR,
    )
)

_register(
    ConversationFlow(
        product_type="capris",
        display_name="Capris",
        greeting="Let's find your capri size! Just a few quick questions.",
        questions=[
            _height_question(),
            _weight_question(),
            _hip_question(required=False, condition="between_sizes"),
            _waist_question(required=False, condition="between_sizes"),
        ],
        between_sizes_advice=_DEFAULT_BETWEEN,
        result_template=_DEFAULT_RESULT,
        out_of_range_template=_DEFAULT_OOR,
    )
)

for _pt, _name in [
    ("shorts", "Shorts"),
    ("bike_shorts", "Bike Shorts"),
    ("opaque_leggings", "Opaque Leggings"),
    ("opaque_capris", "Opaque Capris"),
    ("high_waist_legging", "High Waist Legging"),
]:
    _register(
        ConversationFlow(
            product_type=_pt,
            display_name=_name,
            greeting=f"Let's find your {_name.lower()} size! Just a few quick questions.",
            questions=[
                _height_question(),
                _weight_question(),
            ],
            between_sizes_advice=_DEFAULT_BETWEEN,
            result_template=_DEFAULT_RESULT,
            out_of_range_template=_DEFAULT_OOR,
        )
    )

# --- Tops with bra (height + weight + hip + waist) ---

_register(
    ConversationFlow(
        product_type="tops_with_bra",
        display_name="Top with Built-in Bra",
        greeting="Let's find your size for the top with built-in bra!",
        questions=[
            _height_question(),
            _weight_question(),
            _hip_question(required=False, condition="between_sizes"),
            _waist_question(required=False, condition="between_sizes"),
        ],
        between_sizes_advice=_DEFAULT_BETWEEN,
        result_template=_DEFAULT_RESULT,
        out_of_range_template=_DEFAULT_OOR,
    )
)

# --- Bras ---

_register(
    ConversationFlow(
        product_type="bras",
        display_name="Bra",
        greeting="Let's find your perfect bra size! I just need two measurements.",
        questions=[
            _bust_question(),
            _underbust_question(),
        ],
        between_sizes_advice=_DEFAULT_BETWEEN,
        result_template=_DEFAULT_RESULT,
        out_of_range_template=_DEFAULT_OOR,
    )
)

# --- Braless tops ---

_register(
    ConversationFlow(
        product_type="braless_tops",
        display_name="Braless Top",
        greeting="Let's find your braless top size!",
        questions=[
            _bust_question(),
            _waist_question(),
        ],
        between_sizes_advice=_DEFAULT_BETWEEN,
        result_template=_DEFAULT_RESULT,
        out_of_range_template=_DEFAULT_OOR,
    )
)

# --- Abdominal band ---

_register(
    ConversationFlow(
        product_type="abdominal_band",
        display_name="Abdominal Band",
        greeting="Let's find your abdominal band size!",
        questions=[
            _waist_question(),
        ],
        between_sizes_advice=_DEFAULT_BETWEEN,
        result_template=_DEFAULT_RESULT,
        out_of_range_template=_DEFAULT_OOR,
    )
)

# --- Arm products ---

for _pt, _name in [
    ("arm_sleeves", "Arm Sleeve"),
    ("armbands", "Armband"),
    ("classic_arm_sleeves", "Classic Arm Sleeve"),
]:
    _register(
        ConversationFlow(
            product_type=_pt,
            display_name=_name,
            greeting=f"Let's find your {_name.lower()} size! I'll need a few arm measurements.",
            questions=[
                _upper_arm_question(),
                _forearm_question(),
                _wrist_question(),
            ],
            between_sizes_advice=_DEFAULT_BETWEEN,
            result_template=_DEFAULT_RESULT,
            out_of_range_template=_DEFAULT_OOR,
        )
    )

# --- Classic armbands (has hand_circumference too) ---

_register(
    ConversationFlow(
        product_type="classic_armbands",
        display_name="Classic Armband",
        greeting="Let's find your classic armband size!",
        questions=[
            MeasurementQuestion(
                id="hand",
                measurement_key="hand_circumference_cm",
                text="What's your hand circumference?",
                help_text="Measure around the widest part of your hand, across the knuckles (not including the thumb).",
                dont_know_response="Wrap a string around your palm at the knuckles and measure it — most hands are 7-9 inches.",
                accept_formats=["cm", "inches"],
                input_type="circumference",
            ),
            _wrist_question(),
            _forearm_question(),
            _upper_arm_question(),
        ],
        between_sizes_advice=_DEFAULT_BETWEEN,
        result_template=_DEFAULT_RESULT,
        out_of_range_template=_DEFAULT_OOR,
    )
)

# --- Gauntlets (palm only) ---

_register(
    ConversationFlow(
        product_type="gauntlets",
        display_name="Gauntlet",
        greeting="Let's find your gauntlet size!",
        questions=[
            MeasurementQuestion(
                id="palm",
                measurement_key="palm_circumference_cm",
                text="What's your palm circumference?",
                help_text="Measure around the widest part of your palm, across the knuckles (not including the thumb).",
                dont_know_response="You can wrap a string around your palm and then measure the string!",
                accept_formats=["cm", "inches"],
                input_type="circumference",
            ),
        ],
        between_sizes_advice=_DEFAULT_BETWEEN,
        result_template=_DEFAULT_RESULT,
        out_of_range_template=_DEFAULT_OOR,
    )
)

# --- Socks ---

_register(
    ConversationFlow(
        product_type="socks",
        display_name="Compression Socks",
        greeting="Let's find your compression sock size! I'll need two quick measurements.",
        questions=[
            _calf_question(),
            _ankle_question(),
        ],
        between_sizes_advice=_DEFAULT_BETWEEN,
        result_template=_DEFAULT_RESULT,
        out_of_range_template=_DEFAULT_OOR,
    )
)

# --- Calf sleeves ---

_register(
    ConversationFlow(
        product_type="calf_sleeves",
        display_name="Calf Sleeve",
        greeting="Let's find your calf sleeve size!",
        questions=[
            _calf_question(),
            _ankle_question(),
        ],
        between_sizes_advice=_DEFAULT_BETWEEN,
        result_template=_DEFAULT_RESULT,
        out_of_range_template=_DEFAULT_OOR,
    )
)

# --- Thigh highs ---

_register(
    ConversationFlow(
        product_type="thigh_highs",
        display_name="Thigh Highs",
        greeting="Let's find your thigh high size! I'll need a few leg measurements.",
        questions=[
            MeasurementQuestion(
                id="thigh",
                measurement_key="thigh_circumference_cm",
                text="What's your thigh circumference?",
                help_text="Measure around the widest part of your upper thigh.",
                dont_know_response="Sit down and measure around the fullest part of your thigh, near the top.",
                accept_formats=["cm", "inches"],
                input_type="circumference",
            ),
            _calf_question(),
            _ankle_question(),
            MeasurementQuestion(
                id="leg_length",
                measurement_key="leg_length_cm",
                text="What's your leg length from floor to upper thigh?",
                help_text="Stand barefoot and measure from the floor up to where you'd want the thigh high to reach.",
                dont_know_response="Stand against a wall and estimate the distance from the floor to your mid-thigh — usually 28-33 inches.",
                accept_formats=["cm", "inches"],
                input_type="circumference",
                required=False,
                condition="between_sizes",
                skip_allowed=True,
            ),
        ],
        between_sizes_advice=_DEFAULT_BETWEEN,
        result_template=_DEFAULT_RESULT,
        out_of_range_template=_DEFAULT_OOR,
    )
)

# --- Men's briefs ---

_register(
    ConversationFlow(
        product_type="mens_briefs",
        display_name="Men's Briefs",
        greeting="Let's find your briefs size!",
        questions=[
            _hip_question(),
            _weight_question(required=False, condition="between_sizes"),
        ],
        between_sizes_advice=_DEFAULT_BETWEEN,
        result_template=_DEFAULT_RESULT,
        out_of_range_template=_DEFAULT_OOR,
    )
)


def get_flow(product_type: str) -> ConversationFlow | None:
    """Look up the conversation flow for a product type."""
    return FLOWS.get(product_type)
