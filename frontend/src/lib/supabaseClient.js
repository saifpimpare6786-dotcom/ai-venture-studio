import { createClient } from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || ''
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || ''

// Initialize the client with the anonymous key.
// Row Level Security (RLS) policies govern write and read access.
export const supabase = createClient(supabaseUrl, supabaseAnonKey)
