import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Drug Repurposing Candidate Finder',
  description: 'Discover approved drugs that may be repurposed for new therapeutic applications',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
