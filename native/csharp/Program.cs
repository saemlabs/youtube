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

    public static Rational operator -(Rational left, Rational right) =>
        new(
            left.Numerator * right.Denominator -
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

    public static bool AreEqual(Rational left, Rational right) =>
        left.Numerator == right.Numerator &&
        left.Denominator == right.Denominator;

    public bool IsZero => Numerator.IsZero;

    public bool WithinLinearBounds =>
        BigInteger.Abs(Numerator) <= 1000 && Denominator <= 1000;

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
    private const string Protocol = "saemphysics.capability.v1";
    private const string Capability = "solve_constant_acceleration";
    private const string LinearSystemCapability = "solve_linear_system";

    private static int Main(string[] args)
    {
        bool coreProtocol = args.Length >= 2 && args[0] == "--core-v1";
        if (!coreProtocol && args.Length != 3)
        {
            Console.Error.WriteLine(
                "usage: saemphysics-kinematics-csharp INITIAL_VELOCITY ACCELERATION TIME\n" +
                "   or: saemphysics-kinematics-csharp --core-v1 " +
                "solve_constant_acceleration INITIAL_VELOCITY ACCELERATION TIME"
            );
            return 2;
        }
        if (coreProtocol && args[1] == LinearSystemCapability)
        {
            try
            {
                return SolveLinearSystem(args);
            }
            catch (ArgumentException error)
            {
                Console.Error.WriteLine(
                    $"saemphysics-kinematics-csharp: {error.Message}"
                );
                return 2;
            }
        }
        if (coreProtocol && (args[1] != Capability || args.Length != 5))
        {
            Console.Error.WriteLine(
                "unsupported capability or invalid argument count in core protocol v1"
            );
            return 2;
        }

        int offset = coreProtocol ? 2 : 0;
        try
        {
            Rational initialVelocity = Rational.ParseBounded(args[offset]);
            Rational acceleration = Rational.ParseBounded(args[offset + 1]);
            Rational time = Rational.ParseBounded(args[offset + 2]);
            if (time.Numerator.Sign < 0)
            {
                throw new ArgumentException("time_s must be non-negative");
            }

            Rational displacement =
                initialVelocity * time +
                (acceleration * time * time) / new Rational(2, 1);
            Rational finalVelocity = initialVelocity + acceleration * time;
            bool displacementCheck = Rational.AreEqual(
                displacement,
                initialVelocity * time +
                    (acceleration * time * time) / new Rational(2, 1)
            );
            bool velocityCheck = Rational.AreEqual(
                finalVelocity,
                initialVelocity + acceleration * time
            );

            if (coreProtocol)
            {
                Console.WriteLine(
                    $$"""{"protocol":"{{Protocol}}","capability":"{{Capability}}","status":"completed","result":{"initial_velocity_m_s":"{{initialVelocity}}","acceleration_m_s2":"{{acceleration}}","time_s":"{{time}}","displacement_m":"{{displacement}}","final_velocity_m_s":"{{finalVelocity}}"},"checks":[{"name":"input_bounds","passed":true},{"name":"displacement_equation","passed":{{displacementCheck.ToString(CultureInfo.InvariantCulture).ToLowerInvariant()}}},{"name":"velocity_equation","passed":{{velocityCheck.ToString(CultureInfo.InvariantCulture).ToLowerInvariant()}}}]}"""
                );
            }
            else
            {
                Console.WriteLine(
                    $$"""{"initial_velocity_m_s":"{{initialVelocity}}","acceleration_m_s2":"{{acceleration}}","time_s":"{{time}}","displacement_m":"{{displacement}}","final_velocity_m_s":"{{finalVelocity}}"}"""
                );
            }
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

    private static int SolveLinearSystem(string[] args)
    {
        if (args.Length < 5 ||
            !Rational.IsIntegerText(args[2]) ||
            !int.TryParse(
                args[2],
                NumberStyles.Integer,
                CultureInfo.InvariantCulture,
                out int size
            ) ||
            size is < 1 or > 3)
        {
            throw new ArgumentException(
                "native linear-system dimension must be 1 through 3"
            );
        }
        if (args.Length != 3 + size * size + size)
        {
            throw new ArgumentException(
                "linear-system argument count does not match dimension"
            );
        }

        Rational[,] matrix = new Rational[size, size];
        Rational[,] augmented = new Rational[size, size + 1];
        int argument = 3;
        for (int row = 0; row < size; row++)
        {
            for (int column = 0; column < size; column++)
            {
                Rational value = Rational.ParseBounded(args[argument++]);
                if (!value.WithinLinearBounds)
                {
                    throw new ArgumentOutOfRangeException(
                        nameof(args),
                        "linear-system input must be a bounded exact rational " +
                            "(numerator +/-1000, denominator <=1000)"
                    );
                }
                matrix[row, column] = value;
                augmented[row, column] = value;
            }
        }
        Rational[] rightHandSide = new Rational[size];
        for (int row = 0; row < size; row++)
        {
            Rational value = Rational.ParseBounded(args[argument++]);
            if (!value.WithinLinearBounds)
            {
                throw new ArgumentOutOfRangeException(
                    nameof(args),
                    "linear-system input must be a bounded exact rational " +
                        "(numerator +/-1000, denominator <=1000)"
                );
            }
            rightHandSide[row] = value;
            augmented[row, size] = value;
        }

        Rational determinant = new(1, 1);
        int rowSwaps = 0;
        for (int column = 0; column < size; column++)
        {
            int pivotRow = column;
            while (pivotRow < size && augmented[pivotRow, column].IsZero)
            {
                pivotRow++;
            }
            if (pivotRow == size)
            {
                throw new ArgumentException(
                    "coefficient matrix is singular; no unique solution exists"
                );
            }
            if (pivotRow != column)
            {
                for (int entry = 0; entry <= size; entry++)
                {
                    (augmented[pivotRow, entry], augmented[column, entry]) =
                        (augmented[column, entry], augmented[pivotRow, entry]);
                }
                rowSwaps++;
            }
            Rational pivot = augmented[column, column];
            determinant *= pivot;
            for (int row = column + 1; row < size; row++)
            {
                Rational factor = augmented[row, column] / pivot;
                for (int entry = column + 1; entry <= size; entry++)
                {
                    augmented[row, entry] -= factor * augmented[column, entry];
                }
                augmented[row, column] = new Rational(0, 1);
            }
        }
        if (rowSwaps % 2 != 0)
        {
            determinant = new Rational(-1, 1) * determinant;
        }

        Rational[] solution = new Rational[size];
        for (int row = size - 1; row >= 0; row--)
        {
            Rational value = augmented[row, size];
            for (int column = row + 1; column < size; column++)
            {
                value -= augmented[row, column] * solution[column];
            }
            solution[row] = value / augmented[row, row];
        }
        Rational[] residuals = new Rational[size];
        for (int row = 0; row < size; row++)
        {
            Rational value = new(0, 1);
            for (int column = 0; column < size; column++)
            {
                value += matrix[row, column] * solution[column];
            }
            residuals[row] = value - rightHandSide[row];
        }

        Console.WriteLine(
            $$"""{"protocol":"{{Protocol}}","capability":"{{LinearSystemCapability}}","status":"completed","result":{"solution":[{{string.Join(",", solution.Select(value => $"\"{value}\""))}}],"determinant":"{{determinant}}","residuals":[{{string.Join(",", residuals.Select(value => $"\"{value}\""))}}]},"checks":[{"name":"linear_system_residual","passed":{{residuals.All(value => value.IsZero).ToString(CultureInfo.InvariantCulture).ToLowerInvariant()}},"details":"A*x - b = ({{string.Join(", ", residuals)}})"}]}"""
        );
        return 0;
    }
}
