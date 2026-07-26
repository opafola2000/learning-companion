import AppBrand from "./AppBrand";

interface AuthLayoutProps {
  subtitle: string;
  children: React.ReactNode;
}

export default function AuthLayout({ subtitle, children }: AuthLayoutProps) {
  return (
    <div className="min-h-screen relative flex items-center justify-center overflow-hidden px-4 py-10">
      <div className="absolute inset-0 bg-gradient-to-br from-violet-950 via-indigo-950 to-slate-900" />
      <div className="absolute -top-24 -left-24 h-72 w-72 rounded-full bg-violet-500/30 blur-3xl" />
      <div className="absolute top-1/3 -right-20 h-80 w-80 rounded-full bg-indigo-500/25 blur-3xl" />
      <div className="absolute -bottom-16 left-1/4 h-64 w-64 rounded-full bg-sky-500/20 blur-3xl" />

      <div className="relative max-w-md w-full">
        <div className="text-center mb-8">
          <AppBrand />
          <p className="text-indigo-100/90 mt-4 text-base">{subtitle}</p>
        </div>

        <div className="rounded-2xl border border-white/15 bg-white/95 backdrop-blur-md shadow-2xl shadow-indigo-950/40 p-8">
          {children}
        </div>
      </div>
    </div>
  );
}
