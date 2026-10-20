using System.Globalization;
using System.Numerics;

internal readonly struct Rational
{
    public Rational(BigInteger numerator, BigInteger denominator)
    {
        if (denominator.IsZero)
        {
            throw new ArgumentException("rational denominator cannot be zero");
        }
        if (denominator.Sign < 0)
        {
            numerator = -numerator;
            denominator = -denominator;
        }
        BigInteger divisor = BigInteger.GreatestCommonDivisor(
            BigInteger.Abs(numerator),
            denominator
        );
        Numerator = numerator / divisor;
        Denominator = denominator / divisor;
    }

    public BigInteger Numerator { get; }
    public BigInteger Denominator { get; }

    public override string ToString() =>
        Denominator.IsOne
            ? Numerator.ToString(CultureInfo.InvariantCulture)
            : $"{Numerator.ToString(CultureInfo.InvariantCulture)}/" +
                Denominator.ToString(CultureInfo.InvariantCulture);

    public static Rational operator +(Rational left, Rational right) =>
        new(
            left.Numerator * right.Denominator +
                right.Numerator * left.Denominator,
            left.Denominator * right.Denominator
        );

    public static Rational operator *(Rational left, Rational right) =>
        new(
            left.Numerator * right.Numerator,
            left.Denominator * right.Denominator
        );

    public static Rational operator /(Rational left, Rational right)
    {
        if (right.Numerator.IsZero)
        {
            throw new ArgumentException("cannot divide by zero");
        }
        return new Rational(
            left.Numerator * right.Denominator,
            left.Denominator * right.Numerator
        );
    }

    public static bool IsIntegerText(string text)
    {
        if (text.Length == 0 || text.Length > 24)
        {
            return false;
        }
        int index = text[0] == '-' ? 1 : 0;
        if (index == text.Length)
        {
            return false;
        }
        for (; index < text.Length; index++)
        {
            if (text[index] is < '0' or > '9')
            {
                return false;
            }
        }
        return true;
    }

    public static Rational ParseBounded(string text)
    {
        string[] parts = text.Split('/');
        if (parts.Length is < 1 or > 2 ||
            !IsIntegerText(parts[0]) ||
            (parts.Length == 2 && !IsIntegerText(parts[1])))
        {
            throw new ArgumentException(
                "inputs must be exact integer or fraction strings"
            );
        }
        BigInteger numerator = BigInteger.Parse(
            parts[0],
            CultureInfo.InvariantCulture
        );
        BigInteger denominator = parts.Length == 1
            ? BigInteger.One
            : BigInteger.Parse(parts[1], CultureInfo.InvariantCulture);
        if (BigInteger.Abs(numerator) > 100000 ||
            denominator <= 0 ||
            denominator > 1000)
        {
            throw new ArgumentOutOfRangeException(
                nameof(text),
                "input exceeds native capability bounds (numerator +/-100000, positive denominator <=1000)"
            );
        }
        return new Rational(numerator, denominator);
    }
}

internal static class Program
{
    private static int Main(string[] args)
    {
        if (args.Length != 3)
        {
            Console.Error.WriteLine(
                "usage: saemphysics-kinematics-csharp INITIAL_VELOCITY ACCELERATION TIME"
            );
            return 2;
        }

        try
        {
            Rational initialVelocity = Rational.ParseBounded(args[0]);
            Rational acceleration = Rational.ParseBounded(args[1]);
            Rational time = Rational.ParseBounded(args[2]);
            if (time.Numerator.Sign < 0)
            {
                throw new ArgumentException("time_s must be non-negative");
            }

            Rational displacement =
                initialVelocity * time +
                (acceleration * time * time) / new Rational(2, 1);
            Rational finalVelocity = initialVelocity + acceleration * time;

            Console.WriteLine(
                $$"""{"initial_velocity_m_s":"{{initialVelocity}}","acceleration_m_s2":"{{acceleration}}","time_s":"{{time}}","displacement_m":"{{displacement}}","final_velocity_m_s":"{{finalVelocity}}"}"""
            );
            return 0;
        }
        catch (ArgumentException error)
        {
            Console.Error.WriteLine(
                $"saemphysics-kinematics-csharp: {error.Message}"
            );
            return 2;
        }
        catch (FormatException error)
        {
            Console.Error.WriteLine(
                $"saemphysics-kinematics-csharp: {error.Message}"
            );
            return 2;
        }
    }
}
