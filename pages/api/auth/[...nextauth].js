import NextAuth from 'next-auth'
import GitHubProvider from 'next-auth/providers/github'

export default NextAuth({
  providers: [
    // Configure GitHub provider in Vercel env: GITHUB_ID, GITHUB_SECRET
    GitHubProvider({
      clientId: process.env.GITHUB_ID || '',
      clientSecret: process.env.GITHUB_SECRET || '',
    }),
  ],
  secret: process.env.NEXTAUTH_SECRET,
  pages: {
    signIn: '/api/auth/signin',
  },
})
