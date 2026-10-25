"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { 
  FaCamera, 
  FaPlane, 
  FaGlobeAmericas, 
  FaMapMarkerAlt, 
  FaHeart, 
  FaComment, 
  FaShareAlt, 
  FaEllipsisH
} from "react-icons/fa";
import { Compass } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";
import { supabase } from "@/lib/supabase";

const LiveTravelCommunity = () => {
  const router = useRouter();
  const { user, isAuthenticated } = useAuth();
  const [posts, setPosts] = useState([
    {
      id: 1,
      author: "Sarah Johnson",
      avatar: "/api/placeholder/64/64",
      location: "Santorini, Greece",
      content: "Just arrived in Santorini! The white buildings against the blue sea are even more stunning in person. Any restaurant recommendations?",
      mediaUrl: "/api/placeholder/600/400",
      mediaType: "image/jpeg",
      timestamp: "2026-05-20T15:30:00Z",
      likes: 24,
      comments: 8
    },
    {
      id: 2,
      author: "Mark Chen",
      avatar: "/api/placeholder/64/64",
      location: "Tokyo, Japan",
      content: "Cherry blossom season is in full swing here in Tokyo! The parks are packed but absolutely worth visiting. Pro tip: Come early in the morning to avoid crowds.",
      mediaUrl: "/api/placeholder/600/400",
      mediaType: "image/jpeg",
      timestamp: "2026-05-19T09:15:00Z",
      likes: 42,
      comments: 12
    }
  ]);
  const [newPost, setNewPost] = useState("");
  const [media, setMedia] = useState(null);
  const [mediaPreview, setMediaPreview] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState("feed");
  const [postError, setPostError] = useState(null);

  const handleMediaChange = (e) => {
    const file = e.target.files[0];
    setMedia(file);
    if (file) {
      const fileURL = URL.createObjectURL(file);
      setMediaPreview(fileURL);
    }
  };

  const handleSubmit = async () => {
    if (!newPost.trim() && !media) return;

    if (!isAuthenticated || !user?.id) {
      router.push(`/login?next=${encodeURIComponent("/livecommu")}`);
      return;
    }

    setIsLoading(true);
    setPostError(null);

    try {
      if (supabase) {
        const { error } = await supabase.from("community_posts").insert({
          user_id: user.id,
          content: newPost.trim(),
        });
        if (error) throw error;
      }

      const newPostObj = {
        id: posts.length + 1,
        author: user.name || "Explorer",
        avatar: "/api/placeholder/64/64",
        location: "Current Location",
        content: newPost,
        mediaUrl: mediaPreview,
        mediaType: media?.type || "",
        timestamp: new Date().toISOString(),
        likes: 0,
        comments: 0,
      };

      setPosts([newPostObj, ...posts]);
      setNewPost("");
      setMedia(null);
      setMediaPreview(null);
    } catch (err) {
      setPostError(err.message || "Failed to publish post.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#FBF9F6] py-24 relative font-sans">
      <div className="absolute inset-0 bg-[radial-gradient(#EAE3D2_1px,transparent_1px)] [background-size:16px_16px] opacity-60"></div>
      
      <main className="max-w-5xl mx-auto px-6 relative z-10 pt-8">
        {/* Header */}
        <div className="text-center mb-12">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#1E3F2E]/10 text-[#1E3F2E] text-[10px] font-bold uppercase tracking-widest border border-[#1E3F2E]/20 mb-3">
            <Compass size={10} /> Explorer Scrapbook
          </span>
          <h1 className="text-4xl md:text-5xl font-bold text-[#1E2229] font-display">Postcards from the Road</h1>
          <p className="text-sm text-[#1E2229]/60 max-w-sm mx-auto mt-2">Share snaps, insights, and queries from intentional travels</p>
          <div className="h-0.5 w-12 bg-[#C85A32] mx-auto mt-4"></div>
        </div>

        <div className="flex flex-col md:flex-row gap-8 items-start">
          {/* Left sidebar */}
          <aside className="w-full md:w-64 shrink-0">
            <div className="bg-white rounded-2xl border border-[#EAE3D2] overflow-hidden sticky top-28 shadow-sm">
              <div className="bg-[#1E3F2E] p-4 text-center text-white relative">
                {/* Decorative post mark */}
                <div className="absolute top-2 right-2 w-8 h-8 rounded-full border border-white/20 flex items-center justify-center text-[8px] font-mono select-none pointer-events-none uppercase">Post</div>
                <div className="h-16 w-16 bg-white/10 rounded-full mx-auto flex items-center justify-center text-white border border-white/30 text-xl font-bold font-display">
                  ME
                </div>
                <h2 className="font-bold font-display text-lg text-white mt-3">Journal Entry</h2>
              </div>
              
              <div className="p-4 text-center border-b border-[#EAE3D2]/50 bg-[#FBF9F6]/50">
                <p className="text-xs font-mono text-[#C85A32] font-bold uppercase">Traveler Stats</p>
                <p className="text-sm font-semibold text-[#1E2229] mt-1">12 entries · 8 destinations</p>
              </div>
              
              <div>
                <ul className="divide-y divide-[#EAE3D2]/40 font-mono text-xs font-bold uppercase tracking-wider">
                  {["Feed", "Explore Stays", "My Journals", "Saved Notes"].map((item, index) => (
                    <li key={index}>
                      <button 
                        className={`w-full text-left py-3.5 px-5 hover:bg-[#FBF9F6] hover:text-[#C85A32] transition-colors ${
                          activeTab === item.toLowerCase().replace(' ', '_') || (index === 0 && activeTab === "feed")
                            ? 'bg-[#FBF9F6] text-[#C85A32] border-l-2 border-[#C85A32]' 
                            : 'text-[#1E2229]/80'
                        }`}
                        onClick={() => setActiveTab(item.toLowerCase().replace(' ', '_'))}
                      >
                        {item}
                      </button>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </aside>

          {/* Main content */}
          <div className="flex-1 space-y-8 w-full">
            {/* Create Post Postcard */}
            {!isAuthenticated && (
              <div className="bg-[#1E3F2E]/5 border border-[#1E3F2E]/20 rounded-xl p-4 text-center text-sm text-[#1E2229]/75 mb-4">
                <Link href="/login?next=%2Flivecommu" className="font-bold text-[#C85A32] hover:underline">
                  Sign in
                </Link>{" "}
                to stamp a postcard to the community.
              </div>
            )}
            {postError && (
              <p className="text-sm text-red-600 mb-4">{postError}</p>
            )}
            <div className={`bg-white rounded-2xl border border-[#EAE3D2] p-6 shadow-sm relative overflow-hidden ${!isAuthenticated ? "opacity-60 pointer-events-none" : ""}`}>
              <div className="absolute -top-3 left-1/2 transform -translate-x-1/2 w-28 h-6 bg-[#C85A32]/10 border-x border-[#C85A32]/25 rotate-1"></div>
              
              <div className="flex items-start gap-4 mb-4 mt-2">
                <div className="h-10 w-10 bg-[#1E3F2E] rounded-full flex items-center justify-center text-white border border-[#EAE3D2] font-bold font-display select-none">
                  ME
                </div>
                <textarea
                  value={newPost}
                  onChange={(e) => setNewPost(e.target.value)}
                  placeholder="Draft a new postcard to the community..."
                  className="flex-1 p-3.5 h-24 bg-[#FBF9F6] border border-[#EAE3D2] rounded-xl focus:border-[#C85A32] outline-none text-sm text-[#1E2229] placeholder-[#1E2229]/40 resize-none font-sans"
                />
              </div>

              {mediaPreview && (
                <div className="relative mb-4 rounded-xl overflow-hidden border border-[#EAE3D2] max-h-64">
                  <button
                    onClick={() => {
                      setMedia(null);
                      setMediaPreview(null);
                    }}
                    className="absolute top-2 right-2 bg-red-500 hover:bg-red-600 text-white p-1 rounded-full w-6 h-6 flex items-center justify-center text-xs transition shadow-md z-10 font-bold"
                  >
                    ✕
                  </button>
                  <img src={mediaPreview} alt="Preview" className="w-full h-full object-cover" />
                </div>
              )}

              <div className="flex items-center justify-between border-t border-[#EAE3D2]/50 pt-4 mt-4">
                <div className="flex gap-4">
                  <div className="relative">
                    <input
                      type="file"
                      accept="image/*,video/*"
                      onChange={handleMediaChange}
                      className="opacity-0 absolute inset-0 w-full h-full cursor-pointer"
                    />
                    <button className="flex items-center text-xs font-bold font-mono text-[#1E3F2E] hover:text-[#C85A32] transition-colors border border-[#EAE3D2] bg-[#FBF9F6]/50 px-3 py-1.5 rounded-lg gap-1.5">
                      <FaCamera /> ADD PHOTO
                    </button>
                  </div>
                </div>
                
                <button
                  onClick={handleSubmit}
                  disabled={isLoading || !isAuthenticated || (!newPost.trim() && !media)}
                  className="bg-[#C85A32] hover:bg-[#A54422] text-white px-5 py-2.5 rounded-lg text-xs font-bold font-mono tracking-wider transition-colors disabled:opacity-50 flex items-center gap-1.5 shadow-sm"
                >
                  {isLoading ? (
                    <>
                      <span className="inline-block w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                      SENDING...
                    </>
                  ) : (
                    <>
                      <FaPlane className="rotate-45" /> STAMP & SEND
                    </>
                  )}
                </button>
              </div>
            </div>

            {/* Posts feed */}
            {posts.length === 0 ? (
              <div className="bg-white border border-[#EAE3D2] rounded-2xl p-12 text-center shadow-sm">
                <div className="text-[#C85A32]/40 mb-4">
                  <FaGlobeAmericas size={40} className="mx-auto" />
                </div>
                <h3 className="text-xl font-bold font-display text-[#1E2229] mb-1">Scrapbook is Empty</h3>
                <p className="text-sm text-[#1E2229]/60 mb-4 font-sans">Be the first to stamp a postcard from your journeys!</p>
              </div>
            ) : (
              <div className="space-y-8">
                {posts.map((post) => (
                  <div key={post.id} className="bg-white rounded-2xl border border-[#EAE3D2] shadow-sm hover:shadow-md transition-shadow duration-300 overflow-hidden relative p-6">
                    <div className="flex flex-col gap-5">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <img 
                            src={post.avatar} 
                            alt={post.author} 
                            className="w-10 h-10 rounded-full object-cover border border-[#EAE3D2] shadow-sm"
                          />
                          <div>
                            <h3 className="font-bold text-[#1E2229] text-base">{post.author}</h3>
                            <div className="flex items-center text-xs font-mono text-[#1E2229]/50 gap-1 mt-0.5">
                              <FaMapMarkerAlt className="text-[#C85A32] text-[10px]" />
                              <span>{post.location}</span>
                              <span className="opacity-45">•</span>
                              <span>{new Date(post.timestamp).toLocaleDateString()}</span>
                            </div>
                          </div>
                        </div>
                        <button className="text-[#1E2229]/40 hover:text-[#1E2229] transition-colors">
                          <FaEllipsisH />
                        </button>
                      </div>

                      <p className="text-sm text-[#1E2229]/80 leading-relaxed font-sans">{post.content}</p>

                      {post.mediaUrl && (
                        <div className="rounded-xl overflow-hidden border border-[#EAE3D2] bg-[#FBF9F6] max-h-96">
                          <img src={post.mediaUrl} alt="" className="w-full h-full object-cover grayscale-[10%] hover:grayscale-0 transition-all duration-300" />
                        </div>
                      )}

                      <div className="flex items-center justify-between pt-4 border-t border-[#EAE3D2]/50 font-mono text-xs font-bold uppercase tracking-wider">
                        <div className="flex gap-6 text-[#1E2229]/70">
                          <button 
                            onClick={() => {
                              const updated = posts.map(p => p.id === post.id ? { ...p, likes: p.likes + 1 } : p);
                              setPosts(updated);
                            }}
                            className="flex items-center gap-1.5 hover:text-[#C85A32] transition-colors"
                          >
                            <FaHeart className="text-[#C85A32]/60" />
                            <span>{post.likes}</span>
                          </button>
                          
                          <button className="flex items-center gap-1.5 hover:text-[#1E3F2E] transition-colors">
                            <FaComment className="text-[#1E3F2E]/60" />
                            <span>{post.comments}</span>
                          </button>
                        </div>
                        
                        <button className="text-[#1E2229]/50 hover:text-[#C85A32] transition-colors">
                          <FaShareAlt />
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
};

export default LiveTravelCommunity;