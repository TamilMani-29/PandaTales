import Link from 'next/link';
import { Footer } from '@/components/layout/footer';

export const metadata = {
  title: 'About Us — Pandora Pages',
  description: 'Learn about Pandora Pages and our mission to create personalised books for children.',
};

export default function AboutPage() {
  return (
    <div className="min-h-screen flex flex-col">
      <main className="flex-1 container mx-auto px-4 py-12 max-w-3xl">
        <h1 className="text-4xl font-bold mb-2 bg-gradient-to-r from-[#6B21A8] to-[#C9A227] bg-clip-text text-transparent">
          About Pandora Pages
        </h1>
        <p className="text-sm text-muted-foreground mb-10">Making every child the hero of their own story</p>

        <div className="prose prose-slate max-w-none space-y-8 text-foreground">

          <section>
            <h2 className="text-xl font-bold mb-3">Our Story</h2>
            <p className="text-muted-foreground leading-relaxed">
              Pandora Pages was born from a simple belief: every child deserves to see themselves as the hero of their
              own adventure. We combine the magic of storytelling with the latest in AI to create fully personalised
              story books and coloring books — books where your child&rsquo;s name, appearance, and world are woven
              into every page.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-bold mb-3">What We Create</h2>
            <p className="text-muted-foreground leading-relaxed">
              We offer two types of personalised books, each thoughtfully crafted for young readers:
            </p>
            <ul className="mt-3 space-y-2 text-muted-foreground list-disc list-inside">
              <li>
                <span className="font-medium text-foreground">Story Books</span> — AI-generated narratives featuring
                your child as the main character, complete with vibrant illustrations tailored to their details.
              </li>
              <li>
                <span className="font-medium text-foreground">Coloring Books</span> — Custom coloring pages built
                around themes your child loves, or drawn from their own photos, ready to print or order.
              </li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-bold mb-3">How It Works</h2>
            <p className="text-muted-foreground leading-relaxed">
              Creating a personalised book takes just a few minutes. You share details about your child — their name,
              age, favourite things — choose a theme or upload a photo, and our system generates a unique book just for
              them. You can preview every page before you order.
            </p>
            <p className="text-muted-foreground leading-relaxed mt-3">
              Books are available as instant digital downloads (PDF) or as professionally printed softcover and
              hardcover editions shipped directly to your door.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-bold mb-3">Our Mission</h2>
            <p className="text-muted-foreground leading-relaxed">
              We believe reading should feel personal. When children see themselves reflected in the stories they read,
              it sparks curiosity, builds confidence, and turns reading into an adventure they want to revisit again
              and again. Our mission is to put every child at the centre of a story they&rsquo;ll treasure.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-bold mb-3">Our Commitment to Safety</h2>
            <p className="text-muted-foreground leading-relaxed">
              We take the privacy and safety of children seriously. Photos and personal details you share are used only
              to generate your book and are never sold or shared with third parties. All content is reviewed to be
              age-appropriate and positive. For more details, please read our{' '}
              <Link href="/privacy" className="text-[#6B21A8] hover:underline font-medium">
                Privacy Policy
              </Link>
              .
            </p>
          </section>

          <section>
            <h2 className="text-xl font-bold mb-3">Based in India</h2>
            <p className="text-muted-foreground leading-relaxed">
              Pandora Pages is proudly based in Chennai, India. We ship printed books across India and offer digital
              downloads worldwide.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-bold mb-3">Get in Touch</h2>
            <p className="text-muted-foreground leading-relaxed">
              We&rsquo;d love to hear from you — whether you have a question about an order, feedback on a book, or
              just want to share how much your child loved their story. Reach us at{' '}
              <a href="mailto:hello@pandorapages.in" className="text-[#6B21A8] hover:underline font-medium">
                hello@pandorapages.in
              </a>
              .
            </p>
          </section>

        </div>

        <div className="mt-12">
          <Link href="/" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
            ← Back to Home
          </Link>
        </div>
      </main>

      <Footer />
    </div>
  );
}
