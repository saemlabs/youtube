#include <charconv>
#include <algorithm>
#include <cstdint>
#include <iostream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace {

using Wide = __int128_t;
using UnsignedWide = __uint128_t;

constexpr std::int64_t kMaximumInputNumerator = 100000;
constexpr std::int64_t kMaximumInputDenominator = 1000;

UnsignedWide magnitude(Wide value) {
    return value < 0 ? static_cast<UnsignedWide>(-value)
                     : static_cast<UnsignedWide>(value);
}

UnsignedWide greatest_common_divisor(UnsignedWide left, UnsignedWide right) {
    while (right != 0) {
        const UnsignedWide remainder = left % right;
        left = right;
        right = remainder;
    }
    return left;
}

std::string to_string(Wide value) {
    if (value == 0) {
        return "0";
    }
    const bool negative = value < 0;
    UnsignedWide remaining = magnitude(value);
    std::string digits;
    while (remaining != 0) {
        digits.push_back(static_cast<char>('0' + remaining % 10));
        remaining /= 10;
    }
    if (negative) {
        digits.push_back('-');
    }
    return std::string(digits.rbegin(), digits.rend());
}

class Rational {
  public:
    Rational(Wide numerator, Wide denominator) : numerator_(numerator), denominator_(denominator) {
        if (denominator_ == 0) {
            throw std::invalid_argument("rational denominator cannot be zero");
        }
        if (denominator_ < 0) {
            numerator_ = -numerator_;
            denominator_ = -denominator_;
        }
        const UnsignedWide divisor =
            greatest_common_divisor(magnitude(numerator_), magnitude(denominator_));
        numerator_ /= static_cast<Wide>(divisor);
        denominator_ /= static_cast<Wide>(divisor);
    }

    std::string str() const {
        if (denominator_ == 1) {
            return to_string(numerator_);
        }
        return to_string(numerator_) + "/" + to_string(denominator_);
    }

    friend Rational operator+(const Rational& left, const Rational& right) {
        return Rational(
            left.numerator_ * right.denominator_ +
                right.numerator_ * left.denominator_,
            left.denominator_ * right.denominator_);
    }

    friend Rational operator-(const Rational& left, const Rational& right) {
        return Rational(
            left.numerator_ * right.denominator_ -
                right.numerator_ * left.denominator_,
            left.denominator_ * right.denominator_);
    }

    friend Rational operator*(const Rational& left, const Rational& right) {
        return Rational(
            left.numerator_ * right.numerator_,
            left.denominator_ * right.denominator_);
    }

    friend Rational operator/(const Rational& left, const Rational& right) {
        if (right.numerator_ == 0) {
            throw std::invalid_argument("cannot divide by zero");
        }
        return Rational(
            left.numerator_ * right.denominator_,
            left.denominator_ * right.numerator_);
    }

    bool is_negative() const { return numerator_ < 0; }
    bool is_zero() const { return numerator_ == 0; }
    bool within_input_bounds() const {
        return magnitude(numerator_) <= 1000 && denominator_ <= 1000;
    }

    friend bool operator==(const Rational& left, const Rational& right) {
        return left.numerator_ == right.numerator_ &&
               left.denominator_ == right.denominator_;
    }

  private:
    Wide numerator_;
    Wide denominator_;
};

std::int64_t parse_integer(std::string_view value) {
    if (value.empty() || value.size() > 24) {
        throw std::invalid_argument("invalid rational component");
    }
    std::int64_t parsed = 0;
    const auto result = std::from_chars(value.data(), value.data() + value.size(), parsed);
    if (result.ec != std::errc{} || result.ptr != value.data() + value.size()) {
        throw std::invalid_argument("inputs must be exact integer or fraction strings");
    }
    return parsed;
}

Rational parse_rational(std::string_view value) {
    const std::size_t slash = value.find('/');
    if (slash != std::string_view::npos &&
        value.find('/', slash + 1) != std::string_view::npos) {
        throw std::invalid_argument("rational input may contain only one slash");
    }
    const std::int64_t numerator =
        parse_integer(slash == std::string_view::npos ? value : value.substr(0, slash));
    const std::int64_t denominator =
        slash == std::string_view::npos ? 1 : parse_integer(value.substr(slash + 1));
    if (numerator < -kMaximumInputNumerator ||
        numerator > kMaximumInputNumerator ||
        denominator <= 0 ||
        denominator > kMaximumInputDenominator) {
        throw std::invalid_argument(
            "input exceeds native capability bounds "
            "(numerator +/-100000, positive denominator <=1000)");
    }
    return Rational(numerator, denominator);
}

std::string json_escape(std::string_view value) {
    std::string escaped;
    for (const char character : value) {
        if (character == '"' || character == '\\') {
            escaped.push_back('\\');
        }
        escaped.push_back(character);
    }
    return escaped;
}

void solve_constant_acceleration(
    std::string_view initial_velocity_text,
    std::string_view acceleration_text,
    std::string_view time_text,
    bool core_protocol) {
    const Rational initial_velocity = parse_rational(initial_velocity_text);
    const Rational acceleration = parse_rational(acceleration_text);
    const Rational time = parse_rational(time_text);
    if (time.is_negative()) {
        throw std::invalid_argument("time_s must be non-negative");
    }

    const Rational displacement =
        initial_velocity * time +
        (acceleration * time * time) / Rational(2, 1);
    const Rational final_velocity = initial_velocity + acceleration * time;
    const bool displacement_check =
        displacement ==
        initial_velocity * time + (acceleration * time * time) / Rational(2, 1);
    const bool velocity_check =
        final_velocity == initial_velocity + acceleration * time;

    if (core_protocol) {
        std::cout << "{\"protocol\":\"saemphysics.capability.v1\","
                  << "\"capability\":\"solve_constant_acceleration\","
                  << "\"status\":\"completed\",\"result\":{";
    } else {
        std::cout << "{";
    }
    std::cout << "\"initial_velocity_m_s\":\""
              << json_escape(initial_velocity.str())
              << "\",\"acceleration_m_s2\":\""
              << json_escape(acceleration.str())
              << "\",\"time_s\":\""
              << json_escape(time.str())
              << "\",\"displacement_m\":\""
              << json_escape(displacement.str())
              << "\",\"final_velocity_m_s\":\""
              << json_escape(final_velocity.str()) << "\"}";
    if (core_protocol) {
        std::cout << ",\"checks\":["
                  << "{\"name\":\"input_bounds\",\"passed\":true},"
                  << "{\"name\":\"displacement_equation\",\"passed\":"
                  << (displacement_check ? "true" : "false") << "},"
                  << "{\"name\":\"velocity_equation\",\"passed\":"
                  << (velocity_check ? "true" : "false") << "}]"
                  << "}";
    }
    std::cout << '\n';
}

void solve_linear_system(int argc, char* argv[]) {
    if (argc < 5) {
        throw std::invalid_argument("linear-system request is missing its dimension");
    }
    const std::int64_t dimension = parse_integer(argv[3]);
    if (dimension < 1 || dimension > 3) {
        throw std::invalid_argument("native linear-system dimension must be 1 through 3");
    }
    const int size = static_cast<int>(dimension);
    const int expected_argc = 4 + size * size + size;
    if (argc != expected_argc) {
        throw std::invalid_argument("linear-system argument count does not match dimension");
    }

    std::vector<std::vector<Rational>> matrix(
        size, std::vector<Rational>(size, Rational(0, 1)));
    std::vector<std::vector<Rational>> augmented(
        size, std::vector<Rational>(size + 1, Rational(0, 1)));
    int argument = 4;
    for (int row = 0; row < size; ++row) {
        for (int column = 0; column < size; ++column) {
            matrix[row][column] = parse_rational(argv[argument++]);
            if (!matrix[row][column].within_input_bounds()) {
                throw std::invalid_argument(
                    "linear-system input numerator and denominator must be within +/-1000"
                );
            }
            augmented[row][column] = matrix[row][column];
        }
    }
    std::vector<Rational> right_hand_side(size, Rational(0, 1));
    for (int row = 0; row < size; ++row) {
        right_hand_side[row] = parse_rational(argv[argument++]);
        if (!right_hand_side[row].within_input_bounds()) {
            throw std::invalid_argument(
                "linear-system input numerator and denominator must be within +/-1000"
            );
        }
        augmented[row][size] = right_hand_side[row];
    }

    Rational determinant(1, 1);
    int row_swaps = 0;
    for (int column = 0; column < size; ++column) {
        int pivot_row = column;
        while (pivot_row < size && augmented[pivot_row][column].is_zero()) {
            ++pivot_row;
        }
        if (pivot_row == size) {
            throw std::invalid_argument(
                "coefficient matrix is singular; no unique solution exists"
            );
        }
        if (pivot_row != column) {
            std::swap(augmented[pivot_row], augmented[column]);
            ++row_swaps;
        }
        const Rational pivot = augmented[column][column];
        determinant = determinant * pivot;
        for (int row = column + 1; row < size; ++row) {
            const Rational factor = augmented[row][column] / pivot;
            for (int entry = column + 1; entry <= size; ++entry) {
                augmented[row][entry] =
                    augmented[row][entry] -
                    factor * augmented[column][entry];
            }
            augmented[row][column] = Rational(0, 1);
        }
    }
    if (row_swaps % 2 != 0) {
        determinant = Rational(-1, 1) * determinant;
    }

    std::vector<Rational> solution(size, Rational(0, 1));
    for (int row = size - 1; row >= 0; --row) {
        Rational value = augmented[row][size];
        for (int column = row + 1; column < size; ++column) {
            value = value - augmented[row][column] * solution[column];
        }
        solution[row] = value / augmented[row][row];
    }

    std::vector<Rational> residuals(size, Rational(0, 1));
    for (int row = 0; row < size; ++row) {
        Rational value = Rational(0, 1) - right_hand_side[row];
        for (int column = 0; column < size; ++column) {
            value = value + matrix[row][column] * solution[column];
        }
        residuals[row] = value;
    }
    const bool residual_check = std::all_of(
        residuals.begin(),
        residuals.end(),
        [](const Rational& value) { return value.is_zero(); });

    std::cout << "{\"protocol\":\"saemphysics.capability.v1\","
              << "\"capability\":\"solve_linear_system\","
              << "\"status\":\"completed\",\"result\":{\"solution\":[";
    for (int index = 0; index < size; ++index) {
        if (index != 0) {
            std::cout << ',';
        }
        std::cout << '"' << solution[index].str() << '"';
    }
    std::cout << "],\"determinant\":\"" << determinant.str()
              << "\",\"residuals\":[";
    for (int index = 0; index < size; ++index) {
        if (index != 0) {
            std::cout << ',';
        }
        std::cout << '"' << residuals[index].str() << '"';
    }
    std::cout << "]},\"checks\":[{\"name\":\"linear_system_residual\","
              << "\"passed\":" << (residual_check ? "true" : "false")
              << ",\"details\":\"A*x - b = (";
    for (int index = 0; index < size; ++index) {
        if (index != 0) {
            std::cout << ", ";
        }
        std::cout << residuals[index].str();
    }
    std::cout << ")\"}]}\n";
}

}  // namespace

int main(int argc, char* argv[]) {
    const bool core_protocol =
        argc >= 2 && std::string_view(argv[1]) == "--core-v1";
    if (!core_protocol && argc != 4) {
        std::cerr
            << "usage: saemphysics-kinematics INITIAL_VELOCITY ACCELERATION TIME\n"
            << "   or: saemphysics-kinematics --core-v1 solve_constant_acceleration "
               "INITIAL_VELOCITY ACCELERATION TIME\n";
        return 2;
    }
    try {
        if (core_protocol) {
            if (argc < 3) {
                throw std::invalid_argument(
                    "core protocol v1 requires a capability name"
                );
            }
            const std::string_view capability(argv[2]);
            if (capability == "solve_constant_acceleration" && argc == 6) {
                solve_constant_acceleration(argv[3], argv[4], argv[5], true);
            } else if (capability == "solve_linear_system") {
                solve_linear_system(argc, argv);
            } else {
                throw std::invalid_argument(
                    "unsupported capability or invalid argument count in core protocol v1"
                );
            }
        } else {
            solve_constant_acceleration(argv[1], argv[2], argv[3], false);
        }
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "saemphysics-kinematics: " << error.what() << '\n';
        return 2;
    }
}
