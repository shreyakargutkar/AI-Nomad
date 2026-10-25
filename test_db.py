from supabase_client import supabase

response = supabase.table("trips").select("*").execute()

print(response.data)