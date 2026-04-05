import Link from 'next/link';
import { Footer } from '@/components/layout/footer';

export const metadata = {
  title: 'Terms of Service — Pandora Pages',
  description: 'The terms and conditions governing use of the Pandora Pages platform.',
};

export default function TermsPage() {
  return (
    <div className="min-h-screen flex flex-col">
      <main className="flex-1 container mx-auto px-4 py-12 max-w-3xl">
        <h1 className="text-4xl font-bold mb-2 bg-gradient-to-r from-[#6B21A8] to-[#C9A227] bg-clip-text text-transparent">
          Terms of Service
        </h1>
        <p className="text-sm text-muted-foreground mb-10">Last updated: March 21, 2026</p>

        <div className="prose prose-slate max-w-none space-y-8 text-foreground">

          <section>
            <h2 className="text-xl font-bold mb-3">1. Acceptance of Terms</h2>
            <p className="text-muted-foreground leading-relaxed">
              By accessing or using the Pandora Pages website (&ldquo;Service&rdquo;) you agree to be bound by these
              Terms of Service. If you do not agree, please do not use the Service. These terms apply to all visitors,
              registered users, and others who access the Service.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-bold mb-3">2. Description of Service</h2>
            <p className="text-muted-foreground leading-relaxed">
              Pandora Pages provides an online platform that allows parents and guardians to create personalised
              children&apos;s story books and coloring books. Books can be ordered as a digital PDF download or as a
              professionally printed physical copy.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-bold mb-3">3. Eligibility</h2>
            <p className="text-muted-foreground leading-relaxed">
              You must be at least 18 years old to create an account and place an order. By using the Service you
              represent that you are 18 or older and that the information you provide is accurate and complete.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-bold mb-3">4. User Accounts</h2>
            <ul className="list-disc pl-5 space-y-2 text-muted-foreground">
              <li>You are responsible for maintaining the confidentiality of your account credentials.</li>
              <li>
                You are responsible for all activity that occurs under your account.
              </li>
              <li>
                You agree to notify us immediately at{' '}
                <a href="mailto:info.pandorapages@gmail.com" className="text-[#6B21A8] underline">
                  info.pandorapages@gmail.com
                </a>{' '}
                if you suspect unauthorised access.
              </li>
              <li>
                We reserve the right to suspend or terminate accounts that violate these Terms.
              </li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-bold mb-3">5. Orders and Payments</h2>
            <ul className="list-disc pl-5 space-y-2 text-muted-foreground">
              <li>
                All prices are listed in Indian Rupees (INR) and are inclusive of applicable taxes unless stated
                otherwise.
              </li>
              <li>
                Payments are processed securely by Razorpay. By placing an order you agree to Razorpay&apos;s terms
                and privacy policy.
              </li>
              <li>
                Once a digital PDF has been generated and dispatched to your email, the order is considered fulfilled
                and is non-refundable unless the file is defective or not delivered.
              </li>
              <li>
                For print orders, cancellations are accepted within 12 hours of placing the order. After that, the
                order enters production and cannot be cancelled.
              </li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-bold mb-3">6. Refund and Replacement Policy</h2>
            <ul className="list-disc pl-5 space-y-2 text-muted-foreground">
              <li>
                <span className="font-medium text-foreground">Digital orders</span>: If you do not receive the PDF
                within 24 hours of payment, contact us and we will re-send it or issue a full refund.
              </li>
              <li>
                <span className="font-medium text-foreground">Print orders</span>: If the printed book arrives damaged
                or with a manufacturing defect, we will replace it at no cost. Please send a photo of the damage to
                us within 7 days of receipt.
              </li>
              <li>
                Refunds are credited to the original payment method within 5–7 business days.
              </li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-bold mb-3">7. Uploaded Content</h2>
            <ul className="list-disc pl-5 space-y-2 text-muted-foreground">
              <li>
                You represent that you have the right to upload all photos and content you submit, and that doing so
                does not infringe the rights of any third party.
              </li>
              <li>
                You grant us a limited licence to use your uploaded photos solely for the purpose of generating and
                delivering your book.
              </li>
              <li>
                You must not upload content that is unlawful, offensive, pornographic, or violates the rights of
                others. We reserve the right to refuse or cancel orders containing such content.
              </li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-bold mb-3">8. Intellectual Property</h2>
            <p className="text-muted-foreground leading-relaxed">
              All templates, illustrations, artwork, software, and content on the Pandora Pages platform are owned by
              or licensed to us and are protected by copyright and other intellectual property laws. You may not
              reproduce, distribute, or create derivative works from our templates or platform content without our
              prior written consent.
            </p>
            <p className="text-muted-foreground leading-relaxed mt-3">
              The final personalised book generated for you is licensed to you for personal, non-commercial use. You
              may print it for your own family but may not resell or commercially reproduce it.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-bold mb-3">9. Delivery</h2>
            <ul className="list-disc pl-5 space-y-2 text-muted-foreground">
              <li>
                <span className="font-medium text-foreground">Digital</span>: Delivered to your email address
                typically within 1 hour of payment.
              </li>
              <li>
                <span className="font-medium text-foreground">Print</span>: Estimated 5–7 business days after
                production confirmation. Delivery timelines may vary based on your location and courier conditions.
                We are not liable for delays caused by courier partners or circumstances beyond our control.
              </li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-bold mb-3">10. Limitation of Liability</h2>
            <p className="text-muted-foreground leading-relaxed">
              To the maximum extent permitted by applicable law, Pandora Pages shall not be liable for any indirect,
              incidental, special, or consequential damages arising from your use of the Service. Our total liability
              for any claim arising from a specific order shall not exceed the amount paid for that order.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-bold mb-3">11. Disclaimer of Warranties</h2>
            <p className="text-muted-foreground leading-relaxed">
              The Service is provided &ldquo;as is&rdquo; without warranties of any kind. We do not warrant that the
              Service will be uninterrupted or error-free. AI-generated content may occasionally contain inaccuracies
              — please review your book before purchasing.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-bold mb-3">12. Changes to Terms</h2>
            <p className="text-muted-foreground leading-relaxed">
              We may revise these Terms at any time. We will notify you of material changes by email or by posting a
              notice on the Service. Your continued use after the effective date of the updated Terms constitutes
              acceptance.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-bold mb-3">13. Governing Law</h2>
            <p className="text-muted-foreground leading-relaxed">
              These Terms shall be governed by and construed in accordance with the laws of India. Any disputes shall
              be subject to the exclusive jurisdiction of the courts located in Chennai, Tamil Nadu.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-bold mb-3">14. Contact Us</h2>
            <p className="text-muted-foreground leading-relaxed">
              For any questions about these Terms, please contact us at{' '}
              <a href="mailto:info.pandorapages@gmail.com" className="text-[#6B21A8] underline">
                info.pandorapages@gmail.com
              </a>
              .
            </p>
          </section>

        </div>

        <div className="mt-12 pt-6 border-t">
          <Link href="/" className="text-sm text-[#6B21A8] hover:underline">
            ← Back to Home
          </Link>
        </div>
      </main>
      <Footer />
    </div>
  );
}
