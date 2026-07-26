interface AppBrandProps {
  variant?: "hero" | "nav";
}

export default function AppBrand({ variant = "hero" }: AppBrandProps) {
  if (variant === "nav") {
    return (
      <span className="inline-flex flex-nowrap items-baseline gap-2 whitespace-nowrap">
        <span className="text-lg sm:text-xl font-bold bg-gradient-to-r from-violet-200 via-indigo-100 to-sky-100 bg-clip-text text-transparent">
          Hanz Learning Companion
        </span>
        <span className="text-xs sm:text-sm font-semibold text-amber-300">| -by Tommy</span>
      </span>
    );
  }

  return (
    <h1 className="inline-flex flex-nowrap items-baseline justify-center gap-2 sm:gap-3 whitespace-nowrap text-xl sm:text-2xl md:text-3xl">
      <span className="font-bold bg-gradient-to-r from-violet-300 via-indigo-200 to-sky-200 bg-clip-text text-transparent">
        Hanz Learning Companion
      </span>
      <span className="text-sm sm:text-base md:text-lg font-semibold text-amber-300">
        | -by Tommy
      </span>
    </h1>
  );
}
