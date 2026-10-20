#include <charconv>
#include <cstdint>
#include <iostream>
#include <stdexcept>
#include <string>
#include <string_view>

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
    std::string_view time_text) {
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

    std::cout << "{\"initial_velocity_m_s\":\""
              << json_escape(initial_velocity.str())
              << "\",\"acceleration_m_s2\":\""
              << json_escape(acceleration.str())
              << "\",\"time_s\":\""
              << json_escape(time.str())
              << "\",\"displacement_m\":\""
              << json_escape(displacement.str())
              << "\",\"final_velocity_m_s\":\""
              << json_escape(final_velocity.str())
              << "\"}\n";
}

}  // namespace

int main(int argc, char* argv[]) {
    if (argc != 4) {
        std::cerr << "usage: saemphysics-kinematics INITIAL_VELOCITY ACCELERATION TIME\n";
        return 2;
    }
    try {
        solve_constant_acceleration(argv[1], argv[2], argv[3]);
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "saemphysics-kinematics: " << error.what() << '\n';
        return 2;
    }
}
