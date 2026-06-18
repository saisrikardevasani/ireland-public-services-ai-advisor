import Link from "next/link";

export default function NotFound() {
  return (
    <div className="min-h-screen bg-cream-100 flex items-center justify-center px-6">
      <div className="text-center max-w-sm">
        <p className="font-serif text-7xl font-bold text-forest-200 mb-4">404</p>
        <h1 className="font-serif text-2xl font-bold text-stone-900 mb-3">Page not found</h1>
        <p className="text-stone-500 text-sm mb-8">
          The page you&apos;re looking for doesn&apos;t exist.
        </p>
        <Link
          href="/"
          className="inline-flex items-center gap-2 bg-forest-800 hover:bg-forest-900 text-white font-medium text-sm px-5 py-2.5 rounded-lg transition-colors"
        >
          Back to home
        </Link>
      </div>
    </div>
  );
}
