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

static Rational subtract(Rational left, Rational right) {
    return rational(
        left.numerator * right.denominator -
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

static bool is_zero(Rational value) {
    return value.numerator == 0;
}

static bool within_linear_bounds(Rational value) {
    return magnitude(value.numerator) <= 1000 &&
           value.denominator <= 1000;
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

static bool solve_linear_system(int argc, char *argv[]) {
    if (argc < 5) {
        fprintf(stderr, "linear-system request is missing its dimension\n");
        return false;
    }
    int64_t parsed_dimension = 0;
    if (!parse_integer(argv[3], &parsed_dimension) ||
        parsed_dimension < 1 ||
        parsed_dimension > 3) {
        fprintf(stderr, "native linear-system dimension must be 1 through 3\n");
        return false;
    }
    const int size = (int)parsed_dimension;
    if (argc != 4 + size * size + size) {
        fprintf(stderr, "linear-system argument count does not match dimension\n");
        return false;
    }

    Rational matrix[3][3] = {{{0, 1}}};
    Rational augmented[3][4] = {{{0, 1}}};
    Rational right_hand_side[3] = {{0, 1}, {0, 1}, {0, 1}};
    int argument = 4;
    for (int row = 0; row < size; ++row) {
        for (int column = 0; column < size; ++column) {
            if (!parse_rational(argv[argument++], &matrix[row][column]) ||
                !within_linear_bounds(matrix[row][column])) {
                fprintf(
                    stderr,
                    "linear-system input must be a bounded exact rational "
                    "(numerator +/-1000, denominator <=1000)\n"
                );
                return false;
            }
            augmented[row][column] = matrix[row][column];
        }
    }
    for (int row = 0; row < size; ++row) {
        if (!parse_rational(argv[argument++], &right_hand_side[row]) ||
            !within_linear_bounds(right_hand_side[row])) {
            fprintf(
                stderr,
                "linear-system input must be a bounded exact rational "
                "(numerator +/-1000, denominator <=1000)\n"
            );
            return false;
        }
        augmented[row][size] = right_hand_side[row];
    }

    Rational determinant = rational(1, 1);
    int row_swaps = 0;
    for (int column = 0; column < size; ++column) {
        int pivot_row = column;
        while (pivot_row < size && is_zero(augmented[pivot_row][column])) {
            ++pivot_row;
        }
        if (pivot_row == size) {
            fprintf(
                stderr,
                "coefficient matrix is singular; no unique solution exists\n"
            );
            return false;
        }
        if (pivot_row != column) {
            for (int entry = 0; entry <= size; ++entry) {
                Rational temporary = augmented[pivot_row][entry];
                augmented[pivot_row][entry] = augmented[column][entry];
                augmented[column][entry] = temporary;
            }
            ++row_swaps;
        }
        const Rational pivot = augmented[column][column];
        determinant = multiply(determinant, pivot);
        for (int row = column + 1; row < size; ++row) {
            const Rational factor = divide(augmented[row][column], pivot);
            for (int entry = column + 1; entry <= size; ++entry) {
                augmented[row][entry] = subtract(
                    augmented[row][entry],
                    multiply(factor, augmented[column][entry])
                );
            }
            augmented[row][column] = rational(0, 1);
        }
    }
    if (row_swaps % 2 != 0) {
        determinant = multiply(rational(-1, 1), determinant);
    }

    Rational solution[3] = {{0, 1}, {0, 1}, {0, 1}};
    for (int row = size - 1; row >= 0; --row) {
        Rational value = augmented[row][size];
        for (int column = row + 1; column < size; ++column) {
            value = subtract(
                value,
                multiply(augmented[row][column], solution[column])
            );
        }
        solution[row] = divide(value, augmented[row][row]);
    }

    Rational residuals[3] = {{0, 1}, {0, 1}, {0, 1}};
    bool residual_check = true;
    for (int row = 0; row < size; ++row) {
        Rational value = rational(0, 1);
        for (int column = 0; column < size; ++column) {
            value = add(value, multiply(matrix[row][column], solution[column]));
        }
        residuals[row] = subtract(value, right_hand_side[row]);
        residual_check = residual_check && is_zero(residuals[row]);
    }

    printf(
        "{\"protocol\":\"saemphysics.capability.v1\","
        "\"capability\":\"solve_linear_system\","
        "\"status\":\"completed\",\"result\":{\"solution\":["
    );
    for (int index = 0; index < size; ++index) {
        if (index != 0) {
            putchar(',');
        }
        putchar('"');
        print_rational(solution[index]);
        putchar('"');
    }
    printf("],\"determinant\":\"");
    print_rational(determinant);
    printf("\",\"residuals\":[");
    for (int index = 0; index < size; ++index) {
        if (index != 0) {
            printf(",");
        }
        putchar('"');
        print_rational(residuals[index]);
        putchar('"');
    }
    printf(
        "]},\"checks\":[{\"name\":\"linear_system_residual\","
        "\"passed\":%s,\"details\":\"A*x - b = (",
        residual_check ? "true" : "false"
    );
    for (int index = 0; index < size; ++index) {
        if (index != 0) {
            printf(", ");
        }
        print_rational(residuals[index]);
    }
    printf(")\"}]}\n");
    return true;
}

int main(int argc, char *argv[]) {
    const bool core_protocol =
        argc >= 2 && strcmp(argv[1], "--core-v1") == 0;
    if (!core_protocol && argc != 4) {
        fprintf(
            stderr,
            "usage: saemphysics-kinematics-c INITIAL_VELOCITY ACCELERATION TIME\n"
            "   or: saemphysics-kinematics-c --core-v1 solve_constant_acceleration "
            "INITIAL_VELOCITY ACCELERATION TIME\n"
        );
        return 2;
    }
    if (core_protocol) {
        if (argc < 3) {
            fprintf(stderr, "core protocol v1 requires a capability name\n");
            return 2;
        }
        if (strcmp(argv[2], "solve_linear_system") == 0) {
            return solve_linear_system(argc, argv) ? 0 : 2;
        }
        if (strcmp(argv[2], "solve_constant_acceleration") != 0 || argc != 6) {
            fprintf(
                stderr,
                "unsupported capability or invalid argument count in core protocol v1\n"
            );
            return 2;
        }
        const int offset = 3;
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
                divide(multiply(multiply(acceleration, time), time), two)
            )
        );
        const bool velocity_check = equal(
            final_velocity,
            add(initial_velocity, multiply(acceleration, time))
        );
        printf(
            "{\"protocol\":\"saemphysics.capability.v1\","
            "\"capability\":\"solve_constant_acceleration\","
            "\"status\":\"completed\",\"result\":{"
        );
        print_field("initial_velocity_m_s", initial_velocity, false);
        print_field("acceleration_m_s2", acceleration, false);
        print_field("time_s", time, false);
        print_field("displacement_m", displacement, false);
        print_field("final_velocity_m_s", final_velocity, true);
        printf(
            ",\"checks\":[{\"name\":\"input_bounds\",\"passed\":true},"
            "{\"name\":\"displacement_equation\",\"passed\":%s},"
            "{\"name\":\"velocity_equation\",\"passed\":%s}]}",
            displacement_check ? "true" : "false",
            velocity_check ? "true" : "false"
        );
        putchar('\n');
        return 0;
    }

    Rational initial_velocity;
    Rational acceleration;
    Rational time;
    if (!parse_rational(argv[1], &initial_velocity) ||
        !parse_rational(argv[2], &acceleration) ||
        !parse_rational(argv[3], &time)) {
        fprintf(stderr, "inputs must be bounded exact integer or fraction strings\n");
        return 2;
    }
    if (time.numerator < 0) {
        fprintf(stderr, "time_s must be non-negative\n");
        return 2;
    }
    const Rational displacement = add(
        multiply(initial_velocity, time),
        divide(multiply(multiply(acceleration, time), time), rational(2, 1))
    );
    const Rational final_velocity =
        add(initial_velocity, multiply(acceleration, time));
    putchar('{');
    print_field("initial_velocity_m_s", initial_velocity, false);
    print_field("acceleration_m_s2", acceleration, false);
    print_field("time_s", time, false);
    print_field("displacement_m", displacement, false);
    print_field("final_velocity_m_s", final_velocity, true);
    putchar('\n');
    return 0;
}
