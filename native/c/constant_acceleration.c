#include <errno.h>
#include <inttypes.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef __int128_t Wide;
typedef __uint128_t UnsignedWide;

typedef struct {
    Wide numerator;
    Wide denominator;
} Rational;

static const int64_t maximum_input_numerator = 100000;
static const int64_t maximum_input_denominator = 1000;

static UnsignedWide magnitude(Wide value) {
    if (value < 0) {
        return (UnsignedWide)(-(value + 1)) + 1;
    }
    return (UnsignedWide)value;
}

static UnsignedWide greatest_common_divisor(
    UnsignedWide left,
    UnsignedWide right
) {
    while (right != 0) {
        const UnsignedWide remainder = left % right;
        left = right;
        right = remainder;
    }
    return left;
}

static Rational rational(Wide numerator, Wide denominator) {
    Rational result;
    if (denominator < 0) {
        numerator = -numerator;
        denominator = -denominator;
    }
    const UnsignedWide divisor =
        greatest_common_divisor(magnitude(numerator), magnitude(denominator));
    result.numerator = numerator / (Wide)divisor;
    result.denominator = denominator / (Wide)divisor;
    return result;
}

static Rational add(Rational left, Rational right) {
    return rational(
        left.numerator * right.denominator +
            right.numerator * left.denominator,
        left.denominator * right.denominator
    );
}

static Rational multiply(Rational left, Rational right) {
    return rational(
        left.numerator * right.numerator,
        left.denominator * right.denominator
    );
}

static Rational divide(Rational left, Rational right) {
    return rational(
        left.numerator * right.denominator,
        left.denominator * right.numerator
    );
}

static bool equal(Rational left, Rational right) {
    return left.numerator == right.numerator &&
           left.denominator == right.denominator;
}

static bool parse_integer(const char *text, int64_t *value) {
    if (text == NULL || text[0] == '\0' || strlen(text) > 24) {
        return false;
    }
    const char *digit = text;
    if (*digit == '-') {
        ++digit;
    }
    if (*digit == '\0') {
        return false;
    }
    for (; *digit != '\0'; ++digit) {
        if (*digit < '0' || *digit > '9') {
            return false;
        }
    }
    errno = 0;
    char *end = NULL;
    const long long parsed = strtoll(text, &end, 10);
    if (errno == ERANGE || end == text || *end != '\0') {
        return false;
    }
    *value = (int64_t)parsed;
    return true;
}

static bool parse_rational(const char *text, Rational *value) {
    const char *slash = strchr(text, '/');
    if (slash != NULL && strchr(slash + 1, '/') != NULL) {
        return false;
    }

    char numerator_text[25];
    const size_t numerator_length =
        slash == NULL ? strlen(text) : (size_t)(slash - text);
    if (numerator_length == 0 || numerator_length >= sizeof(numerator_text)) {
        return false;
    }
    memcpy(numerator_text, text, numerator_length);
    numerator_text[numerator_length] = '\0';

    int64_t numerator = 0;
    int64_t denominator = 1;
    if (!parse_integer(numerator_text, &numerator)) {
        return false;
    }
    if (slash != NULL && !parse_integer(slash + 1, &denominator)) {
        return false;
    }
    if (numerator < -maximum_input_numerator ||
        numerator > maximum_input_numerator ||
        denominator <= 0 ||
        denominator > maximum_input_denominator) {
        return false;
    }
    *value = rational(numerator, denominator);
    return true;
}

static void print_wide(Wide value) {
    char digits[48];
    size_t count = 0;
    const bool negative = value < 0;
    UnsignedWide remaining = magnitude(value);
    do {
        digits[count++] = (char)('0' + remaining % 10);
        remaining /= 10;
    } while (remaining != 0);
    if (negative) {
        putchar('-');
    }
    while (count > 0) {
        putchar(digits[--count]);
    }
}

static void print_rational(Rational value) {
    print_wide(value.numerator);
    if (value.denominator != 1) {
        putchar('/');
        print_wide(value.denominator);
    }
}

static void print_field(const char *name, Rational value, bool final_field) {
    printf("\"%s\":\"", name);
    print_rational(value);
    printf(final_field ? "\"}" : "\",");
}

int main(int argc, char *argv[]) {
    const bool core_protocol =
        argc == 6 && strcmp(argv[1], "--core-v1") == 0;
    if (!core_protocol && argc != 4) {
        fprintf(
            stderr,
            "usage: saemphysics-kinematics-c INITIAL_VELOCITY ACCELERATION TIME\n"
            "   or: saemphysics-kinematics-c --core-v1 solve_constant_acceleration "
            "INITIAL_VELOCITY ACCELERATION TIME\n"
        );
        return 2;
    }
    const int offset = core_protocol ? 3 : 1;
    if (core_protocol &&
        strcmp(argv[2], "solve_constant_acceleration") != 0) {
        fprintf(stderr, "unsupported capability in core protocol v1\n");
        return 2;
    }

    Rational initial_velocity;
    Rational acceleration;
    Rational time;
    if (!parse_rational(argv[offset], &initial_velocity) ||
        !parse_rational(argv[offset + 1], &acceleration) ||
        !parse_rational(argv[offset + 2], &time)) {
        fprintf(stderr, "inputs must be bounded exact integer or fraction strings\n");
        return 2;
    }
    if (time.numerator < 0) {
        fprintf(stderr, "time_s must be non-negative\n");
        return 2;
    }

    const Rational two = rational(2, 1);
    const Rational displacement = add(
        multiply(initial_velocity, time),
        divide(multiply(multiply(acceleration, time), time), two)
    );
    const Rational final_velocity =
        add(initial_velocity, multiply(acceleration, time));
    const bool displacement_check = equal(
        displacement,
        add(
            multiply(initial_velocity, time),
            divide(
                multiply(multiply(acceleration, time), time),
                two
            )
        )
    );
    const bool velocity_check = equal(
        final_velocity,
        add(initial_velocity, multiply(acceleration, time))
    );

    if (core_protocol) {
        printf(
            "{\"protocol\":\"saemphysics.capability.v1\","
            "\"capability\":\"solve_constant_acceleration\","
            "\"status\":\"completed\",\"result\":{"
        );
    } else {
        putchar('{');
    }
    print_field("initial_velocity_m_s", initial_velocity, false);
    print_field("acceleration_m_s2", acceleration, false);
    print_field("time_s", time, false);
    print_field("displacement_m", displacement, false);
    print_field("final_velocity_m_s", final_velocity, true);
    if (core_protocol) {
        printf(
            ",\"checks\":[{\"name\":\"input_bounds\",\"passed\":true},"
            "{\"name\":\"displacement_equation\",\"passed\":%s},"
            "{\"name\":\"velocity_equation\",\"passed\":%s}]}",
            displacement_check ? "true" : "false",
            velocity_check ? "true" : "false"
        );
    }
    putchar('\n');
    return 0;
}
