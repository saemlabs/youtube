"""Manim preview of one verified, synthetic constant-acceleration lesson."""

from fractions import Fraction

from manim import (
    BLUE,
    GREEN,
    LEFT,
    ORANGE,
    RIGHT,
    UP,
    WHITE,
    YELLOW,
    Arrow,
    Circle,
    Create,
    FadeIn,
    FadeOut,
    Line,
    Rectangle,
    Scene,
    Text,
    ValueTracker,
    VGroup,
    Write,
    always_redraw,
    linear,
)

from saemphysics.ir import SemanticIR, compile_request
from saemphysics.runtime import RuntimeResult, execute_plan
from saemphysics.visuals.kinematics import ConstantAccelerationMotion


INITIAL_VELOCITY_M_S = "2"
ACCELERATION_M_S2 = "3"
DURATION_S = "4"
MOTION_SECONDS = 8
TRACK_LEFT_X = -5.2
TRACK_RIGHT_X = 5.2
TRACK_Y = -0.8


def verified_motion() -> tuple[RuntimeResult, ConstantAccelerationMotion]:
    request = SemanticIR(
        operation="solve_constant_acceleration",
        question_id="synthetic_cart_motion",
        initial_velocity_m_s=INITIAL_VELOCITY_M_S,
        acceleration_m_s2=ACCELERATION_M_S2,
        time_s=DURATION_S,
    )
    runtime_result = execute_plan(compile_request(request))
    motion = ConstantAccelerationMotion.from_verified_result(
        runtime_result.result,
        runtime_result.verification,
    )
    return runtime_result, motion


class ConstantAccelerationLesson(Scene):
    def construct(self) -> None:
        runtime_result, motion = verified_motion()
        result = runtime_result.result
        final_displacement = motion.at(motion.duration_s).displacement_m
        midpoint_displacement = final_displacement / 2
        initial_velocity = motion.at(0).velocity_m_s
        final_velocity = motion.at(motion.duration_s).velocity_m_s
        if (
            initial_velocity < 0
            or final_velocity < 0
            or final_displacement <= 0
        ):
            raise ValueError(
                "This preview requires forward motion with non-negative velocity"
            )

        title = Text("How far does the cart travel?", font_size=38)
        question = Text(
            f"It starts at {result.initial_velocity_m_s} m/s and accelerates "
            f"at {result.acceleration_m_s2} m/s^2 for {result.time_s} s.",
            font_size=25,
        ).next_to(title, DOWN, buff=0.35)
        self.play(Write(title), FadeIn(question))
        self.wait(3)

        assumption = Text(
            "Model: one-dimensional motion with constant acceleration.",
            font_size=24,
        ).to_edge(UP)
        self.play(FadeOut(title), FadeOut(question), FadeIn(assumption))
        self.wait(3)

        track = Line(
            [TRACK_LEFT_X, TRACK_Y, 0],
            [TRACK_RIGHT_X, TRACK_Y, 0],
            color=WHITE,
        )
        zero_label = Text("0 m", font_size=18).next_to(
            [TRACK_LEFT_X, TRACK_Y, 0], DOWN, buff=0.25
        )
        midpoint_label = Text(f"{midpoint_displacement} m", font_size=18).next_to(
            [0, TRACK_Y, 0], DOWN, buff=0.25
        )
        final_label = Text(f"{final_displacement} m", font_size=18).next_to(
            [TRACK_RIGHT_X, TRACK_Y, 0], DOWN, buff=0.25
        )
        scale_note = Text(
            "Track position is scaled to displacement; velocity arrow length tracks speed.",
            font_size=18,
        ).to_edge(DOWN)

        cart = VGroup(
            Rectangle(width=0.7, height=0.35, color=BLUE, fill_opacity=1),
            Circle(radius=0.11, color=YELLOW, fill_opacity=1).shift(
                LEFT * 0.2 + DOWN * 0.23
            ),
            Circle(radius=0.11, color=YELLOW, fill_opacity=1).shift(
                RIGHT * 0.2 + DOWN * 0.23
            ),
        )
        time_tracker = ValueTracker(0)

        def track_x() -> float:
            state = motion.at(Fraction(str(time_tracker.get_value())))
            displacement = float(state.displacement_m)
            total_displacement = float(final_displacement)
            if total_displacement == 0:
                return TRACK_LEFT_X
            fraction = displacement / total_displacement
            return TRACK_LEFT_X + fraction * (TRACK_RIGHT_X - TRACK_LEFT_X)

        cart.add_updater(lambda item: item.move_to([track_x(), TRACK_Y, 0]))
        elapsed_label = always_redraw(
            lambda: Text(
                f"t = {time_tracker.get_value():.1f} s",
                font_size=22,
            ).to_corner(UP + LEFT)
        )
        velocity_arrow = always_redraw(
            lambda: Arrow(
                start=[track_x(), TRACK_Y + 0.85, 0],
                end=[
                    track_x()
                    + 0.06 * float(
                        motion.at(
                            Fraction(str(time_tracker.get_value()))
                        ).velocity_m_s
                    ),
                    TRACK_Y + 0.85,
                    0,
                ],
                buff=0,
                color=GREEN,
                stroke_width=5,
                max_tip_length_to_length_ratio=0.3,
            )
        )
        velocity_label = Text("v", font_size=23, color=GREEN)
        velocity_label.add_updater(
            lambda label: label.move_to(
                [track_x() + 0.15, TRACK_Y + 1.25, 0]
            )
        )

        self.play(
            Create(track),
            FadeIn(cart),
            FadeIn(zero_label),
            FadeIn(midpoint_label),
            FadeIn(final_label),
            FadeIn(scale_note),
            FadeIn(elapsed_label),
            FadeIn(velocity_arrow),
            FadeIn(velocity_label),
        )
        self.play(
            time_tracker.animate.set_value(float(motion.duration_s)),
            run_time=MOTION_SECONDS,
            rate_func=linear,
        )
        self.wait(1)
        cart.clear_updaters()
        velocity_label.clear_updaters()
        self.play(
            FadeOut(assumption),
            FadeOut(track),
            FadeOut(cart),
            FadeOut(zero_label),
            FadeOut(midpoint_label),
            FadeOut(final_label),
            FadeOut(scale_note),
            FadeOut(elapsed_label),
            FadeOut(velocity_arrow),
            FadeOut(velocity_label),
        )

        derivation_title = Text("Use the constant-acceleration model", font_size=30)
        displacement_line = Text(
            f"s = ut + 1/2 at^2 = {result.displacement_m} m",
            font_size=30,
        )
        velocity_line = Text(
            f"v = u + at = {result.final_velocity_m_s} m/s",
            font_size=30,
        )
        derivation = VGroup(
            derivation_title,
            displacement_line,
            velocity_line,
        ).arrange(DOWN, buff=0.45)
        self.play(Write(derivation))
        self.wait(4)

        checks_title = Text("Independent equation checks", font_size=29)
        checks = VGroup(
            Text("s - (ut + 1/2 at^2) = 0 m", font_size=26, color=GREEN),
            Text("v - (u + at) = 0 m/s", font_size=26, color=GREEN),
        ).arrange(DOWN, buff=0.4)
        check_group = VGroup(checks_title, checks).arrange(DOWN, buff=0.55)
        self.play(FadeOut(derivation), FadeIn(check_group))
        self.wait(3)

        recap = Text(
            f"In {result.time_s} s, the cart travels {result.displacement_m} m "
            f"and reaches {result.final_velocity_m_s} m/s.",
            font_size=27,
            color=ORANGE,
        )
        self.play(FadeOut(check_group), Write(recap))
        self.wait(4)
