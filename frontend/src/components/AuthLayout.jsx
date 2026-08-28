export default function AuthLayout({ title, subtitle, children, footer }) {
  return (
    <main className="flex min-h-dvh items-center justify-center bg-slate-50 px-4 py-8 sm:px-6">
      <section className="w-full max-w-md rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200 sm:p-8">
        <header className="mb-6 text-center">
          <p className="mb-2 text-sm font-semibold text-teal-700">فروش و ویزیت</p>
          <h1 className="text-2xl font-bold text-slate-900">{title}</h1>
          {subtitle && <p className="mt-2 text-sm leading-6 text-slate-600">{subtitle}</p>}
        </header>
        {children}
        {footer && <footer className="mt-6 text-center text-sm text-slate-600">{footer}</footer>}
      </section>
    </main>
  );
}
