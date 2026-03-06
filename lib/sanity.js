// Minimal Sanity client wrapper — requires SANITY_PROJECT_ID, SANITY_DATASET, SANITY_TOKEN env vars
import sanityClient from '@sanity/client'

export const sanity = sanityClient({
  projectId: process.env.SANITY_PROJECT_ID || '',
  dataset: process.env.SANITY_DATASET || 'production',
  apiVersion: '2024-01-01',
  token: process.env.SANITY_TOKEN || '',
  useCdn: false,
})
