import { useState, useEffect } from "react";
import {
  clearToken,
  createDigitalPaymentOrder,
  getDigitalBookCategories,
  getCurrentUser,
  getDigitalBooks,
  getDigitalBookPreview,
  initiatePersonalizedBookOrder,
  loginUser,
  registerUser,
  setToken,
  verifyDigitalPayment,
} from "./lib/api";

const COLLECTIONS = [
  { id:"talecraft", name:"TaleCraft", tag:"Personalised Story Books", emoji:"📖", color:"#FF6B6B", grad:"linear-gradient(135deg,#FF6B6B,#EE5A24)", desc:"Your child's name, world & imagination woven into a stunning illustrated storybook. Every book is uniquely theirs — a gift treasured forever.", personalized:true },
  { id:"personacolor", name:"PersonaColor", tag:"Personalised Coloring Books with Your Photo", emoji:"🎨", color:"#A29BFE", grad:"linear-gradient(135deg,#A29BFE,#6C5CE7)", desc:"Upload your child's photo — we turn it into beautiful coloring art pages. Pick a magical theme & get a one-of-a-kind coloring book made just for them.", personalized:true },
  { id:"skillsprint", name:"SkillSprint", tag:"21-Day Challenge Books", emoji:"⚡", color:"#FFB830", grad:"linear-gradient(135deg,#FFB830,#E67E22)", desc:"21-day workbooks. One skill, daily missions, epic certificate at the end. Kids actually finish these — and beg for more." },
  { id:"rootstales", name:"RootsTales", tag:"Indian Heritage Story Books", emoji:"🪔", color:"#E17055", grad:"linear-gradient(135deg,#E17055,#D63031)", desc:"Ancient stories, festivals & heroes of India retold for today's global kids. Beautiful modern illustrations, timeless wisdom." },
  { id:"moneyminds", name:"MoneyMinds", tag:"Financial Literacy for Kids", emoji:"💰", color:"#00B894", grad:"linear-gradient(135deg,#00B894,#00CEC9)", desc:"The most important subject schools don't teach — money. Real financial skills through stories, games, and activities kids aged 5–15 love." },
  { id:"buildbrain", name:"BuildBrain", tag:"STEM Activity Books", emoji:"🧠", color:"#0984E3", grad:"linear-gradient(135deg,#0984E3,#74B9FF)", desc:"Hands-on science, coding & engineering activity books with real experiments kids can do at home. No special equipment needed." },
  { id:"artvault", name:"ArtVault", tag:"Art & Creativity Books", emoji:"🚀", color:"#E84393", grad:"linear-gradient(135deg,#E84393,#FD79A8)", desc:"From first doodles to gallery-worthy masterpieces — structured art books that grow creativity, confidence and joy." },
  { id:"kidsceo", name:"KidsCEO", tag:"Young Entrepreneur Workbooks", emoji:"👔", color:"#FDCB6E", grad:"linear-gradient(135deg,#FDCB6E,#F39C12)", desc:"12-week workbooks that teach kids to think like entrepreneurs. Business plans, budgets & real projects from day one." },
  { id:"lifepath", name:"LifePath Board", tag:"A3 Life-Skills Snake & Ladder Cards", emoji:"🎲", color:"#00CEC9", grad:"linear-gradient(135deg,#00CEC9,#81ECEC)", desc:"Giant A3 printed game card — 25 squares of life skills, money wisdom, challenges & fun. Roll the dice, land on a square, DO the challenge!" },
  { id:"lifeready", name:"LifeReady", tag:"Real-Life Skills Schools Never Teach", emoji:"🌟", color:"#6C5CE7", grad:"linear-gradient(135deg,#6C5CE7,#A29BFE)", desc:"From tying shoes to managing emotions, making friends to handling failure — practical, emotional and social skills that shape who they become." },
  { id:"mindfulkids", name:"MindfulKids", tag:"Calm, Focus & Well-Being for Children", emoji:"🧘", color:"#26C6DA", grad:"linear-gradient(135deg,#26C6DA,#00838F)", desc:"Breathing exercises, mindfulness activities and calming stories that help children manage anxiety, build focus and sleep better every night." },
];

const BOOKS = {
  talecraft:[
    {id:101,title:"The Brave Quest",price:399,age:"3–8",pages:24,style:"Watercolor",emoji:"🏰",rat:4.9,rev:189,desc:"A thrilling kingdom adventure where your child defeats the shadow dragon and restores light to the land."},
    {id:102,title:"Enchanted Forest",price:399,age:"4–9",pages:28,style:"Animation",emoji:"🌳",rat:4.8,rev:145,desc:"Your child discovers a secret forest where animals talk, trees sing, and magic awaits around every corner."},
    {id:103,title:"Space Captain",price:449,age:"5–10",pages:32,style:"Pop Art",emoji:"🚀",rat:4.9,rev:210,desc:"Blast off to save Planet Zoop! Your child commands the starship through asteroid fields and alien encounters."},
    {id:104,title:"Ocean Rescue",price:399,age:"3–7",pages:24,style:"Watercolor",emoji:"🌊",rat:4.7,rev:98,desc:"Dive deep with dolphins and sea turtles as your child becomes the hero who saves the coral reef."},
  ],
  personacolor:[
    {id:201,title:"My Magical World",price:199,age:"3–7",pages:10,style:"Line Art",emoji:"🧚",rat:4.9,rev:267,desc:"10 enchanting scenes — castles, dragons, fairies — all featuring your child's face as the main character."},
    {id:202,title:"Superhero Me!",price:199,age:"4–9",pages:10,style:"Comic",emoji:"🦸",rat:4.8,rev:198,desc:"Your child becomes a superhero across 10 action-packed scenes. Color your own powers and costume!"},
    {id:203,title:"Animal Friends",price:199,age:"2–6",pages:10,style:"Cute",emoji:"🐾",rat:4.7,rev:156,desc:"Your little one surrounded by adorable animals — pandas, kittens, bunnies — in beautiful coloring scenes."},
    {id:204,title:"Royal Adventures",price:199,age:"3–8",pages:10,style:"Fantasy",emoji:"👑",rat:4.9,rev:234,desc:"Tiaras, castles, magical gardens — your child as the princess or prince of a fairy tale kingdom."},
  ],
  skillsprint:[
    {id:301,title:"21-Day Drawing Challenge",price:149,age:"5–10",pages:24,style:"Activity",emoji:"✏️",rat:4.8,rev:134,desc:"One drawing mission per day for 21 days. By the end, your child will have a full portfolio!"},
    {id:302,title:"21-Day Kindness Challenge",price:129,age:"4–9",pages:24,style:"Guided",emoji:"💖",rat:4.9,rev:189,desc:"Daily kindness missions that build empathy, gratitude and emotional intelligence. With certificate!"},
    {id:303,title:"21-Day Science Explorer",price:149,age:"6–12",pages:24,style:"Experiment",emoji:"🔬",rat:4.7,rev:98,desc:"Real experiments with household items. Volcanoes, crystals, slime — one discovery per day!"},
    {id:304,title:"21-Day Reading Champion",price:129,age:"5–10",pages:24,style:"Tracker",emoji:"📚",rat:4.8,rev:167,desc:"Build a daily reading habit with fun trackers, book reviews and a champion certificate at the end."},
  ],
  rootstales:[
    {id:401,title:"Tales of Ganesha",price:99,age:"4–8",pages:12,style:"Pencil Art",emoji:"🐘",rat:5.0,rev:345,desc:"Beautifully illustrated stories of Lord Ganesha — wisdom, humor, and divine adventures for young minds."},
    {id:402,title:"Hanuman's Great Leap",price:129,age:"5–10",pages:14,style:"Pencil Art",emoji:"🙏",rat:4.9,rev:312,desc:"The epic story of Hanuman's leap across the ocean — courage, devotion, and divine strength."},
    {id:403,title:"Krishna's Butter Adventures",price:99,age:"2–6",pages:10,style:"Animation",emoji:"🧈",rat:5.0,rev:389,desc:"Little Krishna's playful butter-stealing adventures — told with love, humor, and vibrant illustrations."},
    {id:404,title:"Festivals of India",price:129,age:"4–9",pages:16,style:"Watercolor",emoji:"🪔",rat:4.8,rev:234,desc:"Diwali, Holi, Pongal, Eid, Christmas — the stories behind India's beautiful festivals."},
  ],
  moneyminds:[
    {id:501,title:"My First Piggy Bank",price:99,age:"4–7",pages:12,style:"Cartoon",emoji:"🐷",rat:4.7,rev:145,desc:"Save, spend, share — the three jars that teach kids money basics through fun stories and activities."},
    {id:502,title:"Save, Spend & Share",price:129,age:"6–10",pages:14,style:"Activity",emoji:"💸",rat:4.8,rev:112,desc:"Real-world money skills through games, budgets, and smart choices. Financial literacy made fun!"},
    {id:503,title:"Lemonade Stand Adventure",price:149,age:"8–12",pages:18,style:"Story",emoji:"🍋",rat:4.9,rev:98,desc:"Start a business from scratch! Costs, pricing, marketing — all through an exciting lemonade stand story."},
    {id:504,title:"Money Math Fun",price:99,age:"5–9",pages:12,style:"Puzzle",emoji:"🧮",rat:4.6,rev:87,desc:"Addition, subtraction, fractions — all through money puzzles that make math feel like a game."},
  ],
  buildbrain:[
    {id:601,title:"Kitchen Science",price:149,age:"5–10",pages:16,style:"Activity",emoji:"🧪",rat:4.8,rev:178,desc:"Volcanoes from baking soda, crystals from sugar, rainbows from milk — real experiments, real fun!"},
    {id:602,title:"Paper Robot Builder",price:129,age:"7–12",pages:14,style:"STEM",emoji:"🤖",rat:4.7,rev:134,desc:"Build working paper mechanisms — levers, pulleys, gears. Engineering basics through hands-on fun!"},
    {id:603,title:"Coding Without Computers",price:149,age:"6–11",pages:18,style:"Logic",emoji:"💻",rat:4.9,rev:167,desc:"Algorithms, loops, debugging — computer science concepts taught through puzzles and board games."},
    {id:604,title:"Math Puzzle Mania",price:99,age:"5–9",pages:12,style:"Puzzle",emoji:"🔢",rat:4.6,rev:98,desc:"Sudoku, logic grids, pattern recognition — brain-building math puzzles kids actually enjoy!"},
  ],
  artvault:[
    {id:701,title:"My First Masterpiece",price:99,age:"3–6",pages:12,style:"Guided",emoji:"🖌️",rat:4.8,rev:201,desc:"Step-by-step drawing for tiny artists. Simple shapes become beautiful art. Confidence grows with every page!"},
    {id:702,title:"Mandala Magic",price:129,age:"6–12",pages:16,style:"Zen",emoji:"🔵",rat:4.9,rev:178,desc:"Calming mandala patterns that develop focus, patience and creativity. Perfect for quiet afternoon art."},
    {id:703,title:"Cartoon Creator",price:149,age:"7–12",pages:18,style:"Tutorial",emoji:"✍️",rat:4.7,rev:145,desc:"Learn to draw your own cartoon characters! Expressions, poses, stories — become a real cartoonist."},
    {id:704,title:"Origami Adventures",price:129,age:"5–10",pages:14,style:"Craft",emoji:"🦢",rat:4.8,rev:123,desc:"Fold cranes, frogs, flowers and boats. Step-by-step origami with beautiful illustrated instructions."},
  ],
  kidsceo:[
    {id:801,title:"My First Business Plan",price:149,age:"8–14",pages:20,style:"Workbook",emoji:"📋",rat:4.8,rev:89,desc:"From idea to execution — a real business plan workbook that turns young dreamers into young doers."},
    {id:802,title:"The Idea Factory",price:129,age:"7–12",pages:16,style:"Creative",emoji:"💡",rat:4.9,rev:112,desc:"100 business ideas for kids + tools to evaluate them. Creativity meets entrepreneurship!"},
    {id:803,title:"Marketing for Mini Moguls",price:149,age:"9–15",pages:18,style:"Guide",emoji:"📢",rat:4.7,rev:78,desc:"Logos, slogans, social media basics — marketing fundamentals through fun, hands-on projects."},
    {id:804,title:"Budget Boss Kids",price:129,age:"8–13",pages:14,style:"Activity",emoji:"📊",rat:4.8,rev:98,desc:"Track income, expenses, savings goals. Real budgeting skills through an engaging workbook format."},
  ],
  lifepath:[
    {id:901,title:"Life Skills Board Classic",price:199,age:"5–12",pages:1,style:"A3 Board",emoji:"🎯",rat:4.9,rev:234,desc:"25 squares of life challenges — cooking, cleaning, empathy, budgeting. Roll, land, DO. Family game night essential!"},
    {id:902,title:"Money Wisdom Board",price:199,age:"7–14",pages:1,style:"A3 Board",emoji:"💎",rat:4.8,rev:178,desc:"Save, invest, budget, donate — financial wisdom in a fun board game format. Snake eats overspending!"},
    {id:903,title:"Friendship Board",price:199,age:"4–10",pages:1,style:"A3 Board",emoji:"🤝",rat:4.9,rev:189,desc:"Empathy, sharing, conflict resolution — social skills through a colorful family board game."},
    {id:904,title:"Science Discovery Board",price:199,age:"6–12",pages:1,style:"A3 Board",emoji:"🔭",rat:4.7,rev:145,desc:"Land on a square = do a real science experiment! 25 experiments in one exciting board game."},
  ],
  lifeready:[
    {id:1001,title:"Feelings & Emotions",price:149,age:"4–8",pages:20,style:"Activity",emoji:"💓",rat:4.9,rev:234,desc:"Name it, tame it, express it — emotional intelligence workbook that helps children understand their feelings."},
    {id:1002,title:"Friendship Skills",price:129,age:"5–10",pages:16,style:"Guided",emoji:"🫂",rat:4.8,rev:189,desc:"Making friends, being kind, handling conflicts — the social skills every child needs but school doesn't teach."},
    {id:1003,title:"My Daily Routine",price:99,age:"4–8",pages:14,style:"Tracker",emoji:"⏰",rat:4.7,rev:167,desc:"Morning routines, bedtime habits, hygiene checklists — building independence one day at a time."},
    {id:1004,title:"Bounce Back!",price:149,age:"7–13",pages:18,style:"Workbook",emoji:"💪",rat:4.9,rev:198,desc:"Failed a test? Lost a match? This workbook teaches kids that falling down is how you learn to fly."},
  ],
};

const Stars=({r})=><span style={{color:"#FFB830",fontSize:13,letterSpacing:1}}>{"★".repeat(Math.floor(r))}{r%1>=.5?"☆":""}<span style={{color:"#ccc"}}>{"★".repeat(5-Math.floor(r)-(r%1>=.5?1:0))}</span></span>;
const parseTags=(value)=>{
  if(!value) return [];
  if(Array.isArray(value)) return value.map(v=>String(v).trim()).filter(Boolean);
  return String(value).split(",").map(v=>v.trim()).filter(Boolean);
};

export default function App(){
  const [pg,setPg]=useState("home");
  const [col,setCol]=useState(null);
  const [book,setBook]=useState(null);
  const [checkout,setCk]=useState(null);
  const [pModal,setPModal]=useState(null);
  const [del,setDel]=useState("email");
  const [contact,setContact]=useState("");
  const [done,setDone]=useState(false);
  const [checkoutError,setCheckoutError]=useState("");
  const [pForm,setPF]=useState({name:"",age:"",gender:"",phone:"",email:"",theme:"",photoFile:null});
  const [pStep,setPStep]=useState(1);
  const [pDone,setPDone]=useState(false);
  const [pSubmitting,setPSubmitting]=useState(false);
  const [pError,setPError]=useState("");
  const [scrolled,setSc]=useState(false);
  const [user,setUser]=useState(null);
  const [profile,setProfile]=useState(null);
  const [digitalBooks,setDigitalBooks]=useState([]);
  const [digitalBooksLoading,setDigitalBooksLoading]=useState(true);
  const [digitalBooksError,setDigitalBooksError]=useState("");
  const [collections,setCollections]=useState([]);
  const [authOpen,setAuthOpen]=useState(false);
  const [authMode,setAuthMode]=useState("signin");
  const [authForm,setAuthForm]=useState({email:"",password:"",fullName:"",referralCode:""});
  const [authErr,setAuthErr]=useState("");
  const [authLoading,setAuthLoading]=useState(false);
  const [personalizeBook,setPersonalizeBook]=useState(null);

  useEffect(()=>{
    (async()=>{
      try{
        const me=await getCurrentUser();
        setUser(me);
        setProfile(me);
      }catch{
        setUser(null);
        setProfile(null);
      }
    })();
  },[]);

  useEffect(()=>{
    if(!user){setProfile(null);return}
    (async()=>{
      setProfile(user);
    })();
  },[user]);

  useEffect(()=>{
    const params = new URLSearchParams(window.location.search || "");
    const ref = (params.get("ref") || "").trim().toUpperCase();
    if(ref){
      setAuthForm((f)=>({...f,referralCode:ref}));
      if(!user){
        setAuthMode("signup");
      }
    }
  },[user]);

  useEffect(()=>{
    (async()=>{
      try{
        const books=await getDigitalBooks();
        setDigitalBooks(Array.isArray(books)?books:[]);
        setDigitalBooksError("");
      }catch{
        setDigitalBooks([]);
        setDigitalBooksError("Could not load digital books from backend.");
      }finally{
        setDigitalBooksLoading(false);
      }
    })();
  },[]);

  useEffect(()=>{
    (async()=>{
      try{
        const categories=await getDigitalBookCategories();
        const mapped=(Array.isArray(categories)?categories:[])
          .filter(c=>c.is_active)
          .map(c=>({
            id:c.category_id,
            name:c.name,
            tags:parseTags(c.tags?.length?c.tags:[]),
            tag:c.label||(c.personalized?"PERSONALIZED":""),
            emoji:c.emoji||"📚",
            color:c.color||"#6C5CE7",
            grad:c.grad||"linear-gradient(135deg,#6C5CE7,#A29BFE)",
            desc:c.description||"",
            personalized:!!c.personalized,
          }));
        mapped.forEach(item=>{if(!item.tag&&item.tags[0])item.tag=item.tags[0];});
        setCollections(mapped);
      }catch{
        setCollections([]);
      }
    })();
  },[]);

  const collectionsData = collections;
  const collectionsCountLabel = `${collectionsData.length} Magical Collections`;

  const submitAuth=async()=>{
    setAuthErr("");setAuthLoading(true);
    try{
      if(authMode==="signup"){
        const data=await registerUser({
          full_name:authForm.fullName,
          email:authForm.email,
          password:authForm.password,
          referral_code: authForm.referralCode?.trim() || undefined,
        });
        setToken(data.access_token);
        setUser(data.user);
      }else{
        const data=await loginUser({email:authForm.email,password:authForm.password});
        setToken(data.access_token);
        setUser(data.user);
      }
      setAuthOpen(false);
      setAuthForm((f)=>({email:"",password:"",fullName:"",referralCode:f.referralCode||""}));
    }catch(e){setAuthErr(e.message||"Authentication failed")}
    finally{setAuthLoading(false)}
  };

  const signOut=async()=>{clearToken();setUser(null);setProfile(null)};

  useEffect(()=>{const h=()=>setSc(window.scrollY>50);window.addEventListener("scroll",h);return()=>window.removeEventListener("scroll",h)},[]);
  useEffect(()=>{window.scrollTo({top:0,behavior:"smooth"})},[pg,col]);

  const go=(p,c)=>{setPg(p);setCol(c||null)};
  const resetCk=()=>{setCk(null);setDel("email");setContact("");setDone(false);setCheckoutError("")};

  const loadRazorpaySdk = () => new Promise((resolve, reject) => {
    if (window.Razorpay) {
      resolve(true);
      return;
    }
    const script = document.createElement("script");
    script.src = "https://checkout.razorpay.com/v1/checkout.js";
    script.async = true;
    script.onload = () => resolve(true);
    script.onerror = () => reject(new Error("Unable to load payment gateway"));
    document.body.appendChild(script);
  });
  const resetP=()=>{setPModal(null);setPF({name:"",age:"",gender:"",phone:"",email:"",theme:"",photoFile:null});setPStep(1);setPDone(false);setPSubmitting(false);setPError("")};

  const R="#4A1FB8",G="#FFB830",L="#A29BFE",D="#1A0A3E",C="#FFF9F0",W="#25D366";
  const referrals = Number(profile?.referral_count || 0);
  const progressToFive = Math.min(referrals,5);
  const progressToTen = Math.min(referrals,10);
  const hasFiveReward = referrals >= 5;
  const hasTenReward = referrals >= 10;

  const Btn=({children,bg,c:cl,onClick,s})=><button onClick={onClick} style={{background:bg||`linear-gradient(135deg,${R},${L})`,color:cl||"#fff",border:"none",padding:"14px 32px",borderRadius:50,fontFamily:"'Baloo 2',cursive",fontSize:"1.05rem",fontWeight:700,cursor:"pointer",display:"inline-flex",alignItems:"center",gap:8,transition:"all .3s",boxShadow:"0 6px 20px rgba(0,0,0,.12)",...(s||{})}}>{children}</button>;

  const Nav=()=><nav style={{position:"fixed",top:0,left:0,right:0,zIndex:1000,display:"flex",alignItems:"center",justifyContent:"space-between",padding:"10px 28px",background:scrolled?"rgba(255,255,255,.95)":"rgba(255,255,255,.85)",backdropFilter:"blur(20px)",borderBottom:`2px solid rgba(74,31,184,${scrolled?.1:.04})`,transition:"all .3s",boxShadow:scrolled?"0 4px 30px rgba(74,31,184,.1)":"none"}}>
    <div onClick={()=>go("home")} style={{display:"flex",alignItems:"center",gap:10,cursor:"pointer",fontFamily:"'Baloo 2',cursive",fontWeight:800,fontSize:"1.45rem",color:R}}><img src="/logo.png" alt="Pandora Pages" style={{height:"1.6em",width:"1.6em",objectFit:"contain",display:"block"}}/><span>Pandora<span style={{color:G}}>Pages</span></span></div>
    <div style={{display:"flex",gap:18,alignItems:"center"}}>
      {[["Products",()=>go("products")],["See the Magic",()=>{go("home");setTimeout(()=>document.getElementById("magic")?.scrollIntoView({behavior:"smooth"}),100)}],["Collections",()=>go("collections")]].map(([t,fn])=><span key={t} onClick={fn} style={{fontWeight:600,fontSize:".9rem",color:D,cursor:"pointer"}}>{t}</span>)}
      <button onClick={()=>{go("home");setTimeout(()=>document.getElementById("refer")?.scrollIntoView({behavior:"smooth"}),120)}} style={{background:`linear-gradient(135deg,${G},#FFC947)`,border:"none",color:D,padding:"7px 16px",borderRadius:30,fontFamily:"'Baloo 2',cursive",fontWeight:800,fontSize:".82rem",cursor:"pointer",boxShadow:"0 4px 14px rgba(255,184,48,.4)",animation:"pulse 2.4s ease-in-out infinite",lineHeight:1.2,whiteSpace:"nowrap",display:"inline-flex",alignItems:"center",gap:6}}>🎁 Refer & Earn</button>
      <a href="https://chat.whatsapp.com/CMevldqAxQEAP0z40jTF5j" target="_blank" rel="noreferrer" style={{background:`linear-gradient(135deg,${W},#1FAF54)`,border:"none",color:"#fff",padding:"7px 16px",borderRadius:30,fontFamily:"'Baloo 2',cursive",fontWeight:800,fontSize:".82rem",cursor:"pointer",boxShadow:"0 4px 14px rgba(37,211,102,.4)",textDecoration:"none",display:"inline-flex",alignItems:"center",gap:6,lineHeight:1.2,whiteSpace:"nowrap",animation:"pulse 2.4s ease-in-out infinite"}}>💬 Join Community</a>
      {user?<>
        <span style={{fontWeight:600,fontSize:".85rem",color:R}}>👋 {profile?.full_name||user.email?.split("@")[0]}</span>
        <button onClick={signOut} style={{background:"transparent",border:`1.5px solid ${R}`,color:R,padding:"7px 16px",borderRadius:30,fontFamily:"inherit",fontWeight:700,fontSize:".82rem",cursor:"pointer"}}>Sign Out</button>
      </>:<>
        <button onClick={()=>{setAuthMode("signin");setAuthErr("");setAuthOpen(true)}} style={{background:"transparent",border:`1.5px solid ${R}`,color:R,padding:"7px 16px",borderRadius:30,fontFamily:"inherit",fontWeight:700,fontSize:".82rem",cursor:"pointer"}}>Sign In</button>
        <button onClick={()=>{setAuthMode("signup");setAuthErr("");setAuthOpen(true)}} style={{background:`linear-gradient(135deg,${R},#6C5CE7)`,border:"none",color:"#fff",padding:"7px 16px",borderRadius:30,fontFamily:"inherit",fontWeight:700,fontSize:".82rem",cursor:"pointer"}}>Sign Up</button>
      </>}
    </div>
  </nav>;

  const WA=()=><a href="https://chat.whatsapp.com/CMevldqAxQEAP0z40jTF5j" target="_blank" rel="noreferrer" style={{position:"fixed",bottom:24,right:24,zIndex:999,width:60,height:60,borderRadius:"50%",background:W,display:"flex",alignItems:"center",justifyContent:"center",boxShadow:"0 6px 25px rgba(37,211,102,.4)",textDecoration:"none",fontSize:28,animation:"waBounce 3s ease-in-out infinite"}}>💬</a>;

  const Card3D=({c})=>{
    const [tilt,setTilt]=useState({x:0,y:0,active:false});
    const onMove=e=>{
      const r=e.currentTarget.getBoundingClientRect();
      const px=(e.clientX-r.left)/r.width-.5;
      const py=(e.clientY-r.top)/r.height-.5;
      setTilt({x:py*-12,y:px*14,active:true,mx:px*100+50,my:py*100+50});
    };
    const onLeave=()=>setTilt({x:0,y:0,active:false});
    return <div onClick={()=>go("collection",c)} onMouseMove={onMove} onMouseLeave={onLeave} style={{position:"relative",cursor:"pointer",perspective:1200,height:340}}>
      <div style={{position:"relative",width:"100%",height:"100%",borderRadius:24,transformStyle:"preserve-3d",transform:`rotateX(${tilt.x}deg) rotateY(${tilt.y}deg) translateZ(0)`,transition:tilt.active?"transform .08s linear":"transform .5s cubic-bezier(.2,.9,.3,1.2)",background:c.grad,boxShadow:tilt.active?`0 30px 60px -15px ${c.color}55, 0 18px 40px -20px rgba(0,0,0,.3)`:`0 14px 30px -10px ${c.color}33`,overflow:"hidden"}}>
        <div style={{position:"absolute",inset:0,background:`radial-gradient(circle at ${tilt.mx||50}% ${tilt.my||50}%, rgba(255,255,255,.35), transparent 55%)`,opacity:tilt.active?1:.5,transition:"opacity .3s",pointerEvents:"none"}}/>
        <div style={{position:"absolute",top:-30,right:-30,width:140,height:140,borderRadius:"50%",background:"rgba(255,255,255,.15)",filter:"blur(2px)"}}/>
        <div style={{position:"absolute",bottom:-40,left:-40,width:120,height:120,borderRadius:"50%",background:"rgba(255,255,255,.12)"}}/>
        <div style={{position:"relative",height:"100%",padding:"26px 24px",display:"flex",flexDirection:"column",justifyContent:"space-between",color:"#fff",transform:"translateZ(40px)"}}>
          <div>
            <div style={{display:"flex",alignItems:"flex-start",justifyContent:"space-between",marginBottom:18}}>
              <div style={{width:64,height:64,borderRadius:18,background:"rgba(255,255,255,.22)",backdropFilter:"blur(10px)",display:"flex",alignItems:"center",justifyContent:"center",fontSize:34,boxShadow:"inset 0 1px 0 rgba(255,255,255,.4), 0 8px 24px rgba(0,0,0,.18)",transform:"translateZ(30px)"}}>{c.emoji}</div>
              {(c.personalized||c.tag)&&<div style={{background:"rgba(255,255,255,.95)",color:c.color,padding:"5px 12px",borderRadius:20,fontSize:".68rem",fontWeight:800,boxShadow:"0 4px 12px rgba(0,0,0,.15)",transform:"translateZ(40px)"}}>{c.tag||"📷 PERSONALIZED"}</div>}
            </div>
            <h3 style={{fontFamily:"'Baloo 2',cursive",fontSize:"1.6rem",color:"#fff",margin:"0 0 4px",textShadow:"0 2px 8px rgba(0,0,0,.15)",transform:"translateZ(20px)"}}>{c.name}</h3>
            {c.tags?.length>0&&<div style={{display:"flex",gap:6,flexWrap:"wrap",margin:"0 0 12px",transform:"translateZ(15px)"}}>{c.tags.map((tag)=><span key={tag} style={{fontSize:".66rem",color:"rgba(255,255,255,.95)",background:"rgba(255,255,255,.2)",padding:"3px 9px",borderRadius:999,fontWeight:700}}>{tag}</span>)}</div>}
            <p style={{fontSize:".88rem",color:"rgba(255,255,255,.92)",lineHeight:1.6,margin:0,display:"-webkit-box",WebkitLineClamp:3,WebkitBoxOrient:"vertical",overflow:"hidden",transform:"translateZ(10px)"}}>{c.desc}</p>
          </div>
          <div style={{display:"flex",alignItems:"center",justifyContent:"space-between",paddingTop:16,borderTop:"1px solid rgba(255,255,255,.25)",transform:"translateZ(25px)"}}>
            <div><div style={{fontSize:".64rem",color:"rgba(255,255,255,.65)",fontWeight:700,letterSpacing:1}}>STARTING</div><div style={{fontFamily:"'Baloo 2',cursive",fontSize:"1.4rem",color:"#fff",fontWeight:800,lineHeight:1}}>₹99</div></div>
            <div style={{background:"rgba(255,255,255,.95)",color:c.color,padding:"10px 18px",borderRadius:30,fontWeight:800,fontSize:".85rem",boxShadow:"0 6px 18px rgba(0,0,0,.18)",display:"flex",alignItems:"center",gap:6}}>Explore <span style={{transition:"transform .3s",display:"inline-block",transform:tilt.active?"translateX(3px)":"translateX(0)"}}>→</span></div>
          </div>
        </div>
      </div>
    </div>;
  };

  const BookCard3D=({b,col,isP,onClick})=>{
    const [tilt,setTilt]=useState({x:0,y:0,active:false,mx:50,my:50});
    const frontCover = b.front_image_url || b.cover_image_url;
    const onMove=e=>{
      const r=e.currentTarget.getBoundingClientRect();
      const px=(e.clientX-r.left)/r.width-.5;
      const py=(e.clientY-r.top)/r.height-.5;
      setTilt({x:py*-14,y:px*16,active:true,mx:px*100+50,my:py*100+50});
    };
    const onLeave=()=>setTilt({x:0,y:0,active:false,mx:50,my:50});
    return <div onClick={onClick} onMouseMove={onMove} onMouseLeave={onLeave} style={{position:"relative",cursor:"pointer",perspective:1400,minHeight:430}}>
      <div style={{position:"relative",width:"100%",height:"auto",minHeight:"100%",borderRadius:22,transformStyle:"preserve-3d",transform:`rotateX(${tilt.x}deg) rotateY(${tilt.y}deg)`,transition:tilt.active?"transform .08s linear":"transform .55s cubic-bezier(.2,.9,.3,1.2)",background:"#fff",boxShadow:tilt.active?`0 32px 70px -18px ${col.color}55, 0 18px 40px -20px rgba(0,0,0,.25)`:`0 10px 30px -8px ${col.color}22, 0 4px 12px rgba(0,0,0,.06)`,overflow:"hidden",border:`1px solid ${col.color}22`}}>
        {/* Cover */}
        <div style={{position:"relative",height:230,background:col.grad,overflow:"hidden",transform:"translateZ(0)"}}>
          {frontCover && (
            <img
              src={frontCover}
              alt={`${b.title} front cover`}
              style={{position:"absolute",inset:0,width:"100%",height:"100%",objectFit:"cover"}}
            />
          )}
          {frontCover && (
            <div style={{position:"absolute",inset:0,background:"linear-gradient(180deg,rgba(0,0,0,.12),rgba(0,0,0,.35))"}} />
          )}
          <div style={{position:"absolute",inset:0,background:`radial-gradient(circle at ${tilt.mx}% ${tilt.my}%, rgba(255,255,255,.4), transparent 55%)`,opacity:tilt.active?1:.4,transition:"opacity .3s",pointerEvents:"none"}}/>
          <div style={{position:"absolute",top:-30,right:-30,width:120,height:120,borderRadius:"50%",background:"rgba(255,255,255,.18)",filter:"blur(2px)"}}/>
          <div style={{position:"absolute",bottom:-30,left:-20,width:90,height:90,borderRadius:"50%",background:"rgba(255,255,255,.12)"}}/>
          <div style={{position:"absolute",left:0,top:0,bottom:0,width:14,background:"linear-gradient(90deg,rgba(0,0,0,.2),transparent)",transform:"translateZ(-1px)"}}/>
          {!frontCover && <div style={{position:"absolute",inset:0,display:"flex",alignItems:"center",justifyContent:"center",fontSize:88,filter:"drop-shadow(0 8px 18px rgba(0,0,0,.25))",transform:`translateZ(50px) scale(${tilt.active?1.06:1})`,transition:"transform .4s"}}>{b.emoji}</div>}
          <div style={{position:"absolute",top:12,left:12,background:"rgba(255,255,255,.95)",color:col.color,padding:"4px 10px",borderRadius:20,fontSize:".68rem",fontWeight:800,boxShadow:"0 4px 12px rgba(0,0,0,.15)",transform:"translateZ(40px)"}}>{b.style}</div>
          <div style={{position:"absolute",bottom:12,right:12,background:"#fff",color:col.color,padding:"6px 14px",borderRadius:30,fontFamily:"'Baloo 2',cursive",fontWeight:800,fontSize:"1.02rem",boxShadow:"0 6px 18px rgba(0,0,0,.2)",transform:"translateZ(50px)"}}>₹{b.price}</div>
          {isP&&<div style={{position:"absolute",top:12,right:12,background:`linear-gradient(135deg,${G},#FFC947)`,color:D,padding:"4px 10px",borderRadius:20,fontSize:".66rem",fontWeight:800,boxShadow:"0 4px 12px rgba(0,0,0,.18)",transform:"translateZ(45px)"}}>📷 PERSONALIZE</div>}
        </div>
        {/* Body */}
        <div style={{padding:"16px 18px 18px",transform:"translateZ(20px)",position:"relative",display:"flex",flexDirection:"column",minHeight:200}}>
          <h3 style={{fontFamily:"'Baloo 2',cursive",fontSize:"1.05rem",color:D,margin:"0 0 5px",lineHeight:1.25}}>{b.title}</h3>
          <div style={{display:"flex",alignItems:"center",gap:5,marginBottom:7}}><Stars r={b.rat}/><span style={{fontSize:".7rem",color:"#999",fontWeight:600}}>{b.rat} ({b.rev})</span></div>
          <p style={{fontSize:".8rem",color:"#777",lineHeight:1.55,display:"-webkit-box",WebkitLineClamp:2,WebkitBoxOrient:"vertical",overflow:"hidden",margin:"0 0 10px"}}>{b.desc}</p>
          {b.tags?.length>0&&<div style={{display:"flex",gap:5,flexWrap:"wrap",marginBottom:8}}>{b.tags.map((tag)=><span key={tag} style={{background:`${col.color}16`,color:col.color,padding:"2px 8px",borderRadius:10,fontSize:".66rem",fontWeight:700}}>{tag}</span>)}</div>}
          <div style={{display:"flex",gap:5,flexWrap:"wrap",marginBottom:10}}>{[b.age,`${b.pages}${b.pages===1?" board":" pg"}`].map(t=><span key={t} style={{background:`${col.color}10`,color:col.color,padding:"3px 9px",borderRadius:10,fontSize:".68rem",fontWeight:700}}>{t}</span>)}</div>
          <div style={{display:"flex",alignItems:"center",justifyContent:"space-between",paddingTop:8,borderTop:`1px solid ${col.color}15`,marginTop:"auto"}}>
            <span style={{fontSize:".75rem",color:"#aaa",fontWeight:600}}>{isP?"Free preview":"Instant delivery"}</span>
            <div style={{background:col.grad,color:"#fff",padding:"6px 14px",borderRadius:30,fontWeight:800,fontSize:".78rem",display:"flex",alignItems:"center",gap:5,boxShadow:`0 6px 14px ${col.color}44`}}>{isP?"Personalize":"Buy"} <span style={{transition:"transform .3s",display:"inline-block",transform:tilt.active?"translateX(3px)":"translateX(0)"}}>→</span></div>
          </div>
        </div>
      </div>
    </div>;
  };

  const Home=()=><div style={{background:C}}>
    <div style={{background:`linear-gradient(90deg,${G},#FFC947,${G})`,padding:12,textAlign:"center",fontFamily:"'Baloo 2',cursive",fontWeight:700,fontSize:".95rem",color:D,backgroundSize:"200% 100%",animation:"shimmer 3s linear infinite",marginTop:56}}>
      🎉 {collectionsCountLabel} now live! Digital Books starting @ ₹99 <span onClick={()=>go("collections")} style={{color:R,textDecoration:"underline",cursor:"pointer",fontWeight:800}}>Browse Now →</span>
    </div>

    <section style={{minHeight:"85vh",display:"flex",alignItems:"center",justifyContent:"center",padding:"60px 28px 80px",background:`linear-gradient(135deg,#F8F0FF,${C},#FFF0E8)`,position:"relative",overflow:"hidden"}}>
      {[{w:260,h:260,c:L,t:-40,r:-40},{w:170,h:170,c:G,b:"12%",l:-20},{w:120,h:120,c:"#FF6B6B",t:"35%",r:"22%"}].map((s,i)=><div key={i} style={{position:"absolute",width:s.w,height:s.h,borderRadius:"50%",background:s.c,opacity:.1,top:s.t,right:s.r,bottom:s.b,left:s.l,animation:`float ${6+i*2}s ease-in-out infinite ${i}s`}}/>)}
      <div style={{maxWidth:1100,width:"100%",display:"grid",gridTemplateColumns:"1fr 1fr",gap:50,alignItems:"center",position:"relative",zIndex:2}}>
        <div>
          <div style={{display:"flex",gap:10,marginBottom:22,flexWrap:"wrap"}}>
            {[["📱 Digital Books @ ₹99","#E8F5E9","#27AE60"],["🎨 Coloring Books @ ₹199","#FFF3E0","#E67E22"],["📖 Story Books @ ₹399","#EDE7FF",R]].map(([t,bg,c])=><span key={t} style={{padding:"5px 14px",borderRadius:30,fontSize:".8rem",fontWeight:600,background:bg,color:c}}>{t}</span>)}
          </div>
          <h1 style={{fontFamily:"'Baloo 2',cursive",fontSize:"clamp(2rem,4.5vw,3.3rem)",lineHeight:1.15,color:D,marginBottom:16}}>
            Your Child Becomes the <span style={{background:`linear-gradient(135deg,${R},${L})`,WebkitBackgroundClip:"text",WebkitTextFillColor:"transparent"}}>Hero</span> of Their Own <span style={{color:G,WebkitTextFillColor:G}}>Story</span>
          </h1>
          <p style={{fontSize:"1.08rem",color:"#555",lineHeight:1.7,marginBottom:26,maxWidth:500}}>Personalized story books & coloring books with your child's <strong>real photo</strong> woven into every page. Plus {collectionsData.length} magical collections starting at just ₹99!</p>
          <div style={{display:"flex",gap:14,flexWrap:"wrap"}}>
            <Btn onClick={()=>go("products")}>✨ Our Products</Btn>
            <Btn bg={G} cl={D} onClick={()=>document.getElementById("magic")?.scrollIntoView({behavior:"smooth"})} s={{boxShadow:"0 6px 20px rgba(255,184,48,.3)",color:D}}>📷 See the Magic</Btn>
          </div>
        </div>
        <div style={{position:"relative",height:420,display:"flex",alignItems:"center",justifyContent:"center"}}>
          {["✨","⭐","💫","🌟","✨"].map((s,i)=><span key={i} style={{position:"absolute",fontSize:18,animation:`float 2s ease-in-out infinite ${i*.4}s`,...[{top:10,right:50},{top:70,right:5},{bottom:50,left:50},{top:"50%",left:5},{bottom:5,right:"35%"}][i]}}>{s}</span>)}
          <div style={{position:"absolute",top:30,left:10,width:185,borderRadius:16,overflow:"hidden",boxShadow:"0 12px 40px rgba(0,0,0,.12)",transform:"rotate(-6deg)",border:"4px solid #fff",background:"#fff"}}>
            <div style={{height:210,background:"linear-gradient(135deg,#FFE8D6,#FFDAB9)",display:"flex",alignItems:"center",justifyContent:"center",fontSize:56}}>👧</div>
            <div style={{padding:10,textAlign:"center",fontFamily:"'Baloo 2',cursive",fontWeight:700,fontSize:".82rem",color:"#E67E22"}}>📸 Upload Real Photo</div>
          </div>
          <div style={{position:"absolute",top:"50%",left:"50%",transform:"translate(-55%,-50%)",zIndex:10,width:65,height:65,borderRadius:"50%",background:`linear-gradient(135deg,${G},#FFD77A)`,display:"flex",alignItems:"center",justifyContent:"center",boxShadow:"0 8px 25px rgba(255,184,48,.4)",animation:"pulse 2s ease-in-out infinite",fontSize:24,color:"#fff",fontWeight:800}}>→</div>
          <div style={{position:"absolute",bottom:10,right:0,width:210,borderRadius:16,overflow:"hidden",boxShadow:`0 18px 50px rgba(74,31,184,.2)`,transform:"rotate(4deg)",border:`4px solid ${G}`,background:"#fff"}}>
            <div style={{height:240,background:`linear-gradient(135deg,#EDE7FF,#C4B5FD,#A78BFA)`,display:"flex",flexDirection:"column",alignItems:"center",justifyContent:"center",padding:14,position:"relative"}}>
              <div style={{position:"absolute",top:8,left:8,background:"rgba(255,255,255,.9)",padding:"2px 8px",borderRadius:16,fontSize:".58rem",fontWeight:700,color:R}}>📷 Real Photo Inside</div>
              <div style={{fontFamily:"'Baloo 2',cursive",fontSize:".85rem",color:"#fff",textAlign:"center",textShadow:"0 2px 6px rgba(0,0,0,.2)",marginBottom:6}}>Princess Ananya<br/><strong style={{fontSize:"1.1rem"}}>& the Dragon!</strong></div>
              <div style={{fontSize:50}}>🦸‍♀️</div>
              <div style={{fontSize:".7rem",color:"rgba(255,255,255,.8)",marginTop:4}}>Her real face in every illustration</div>
            </div>
            <div style={{padding:10,textAlign:"center",background:`linear-gradient(135deg,${R},${L})`,fontFamily:"'Baloo 2',cursive",fontWeight:700,fontSize:".85rem",color:"#fff"}}>Her face is IN the book!</div>
          </div>
        </div>
      </div>
    </section>

    <div style={{background:"#fff",padding:"32px 20px",display:"flex",justifyContent:"center",gap:50,flexWrap:"wrap",borderTop:"1px solid rgba(74,31,184,.05)",borderBottom:"1px solid rgba(74,31,184,.05)"}}>
      {[["500+","Books Created"],[String(collectionsData.length),"Collections"],["₹99","Starting From"],["📷","Real Photo Books"]].map(([n,l])=><div key={l} style={{display:"flex",alignItems:"center",gap:8}}><span style={{fontFamily:"'Baloo 2',cursive",fontSize:"1.7rem",fontWeight:800,background:`linear-gradient(135deg,${R},${L})`,WebkitBackgroundClip:"text",WebkitTextFillColor:"transparent"}}>{n}</span><span style={{fontSize:".83rem",color:"#777",fontWeight:600,lineHeight:1.2}}>{l}</span></div>)}
    </div>

    <section id="magic" style={{padding:"90px 28px",background:"#fff",overflow:"hidden"}}>
      <div style={{maxWidth:1100,margin:"0 auto",display:"grid",gridTemplateColumns:"1fr 1fr",gap:70,alignItems:"center"}}>
        <div style={{position:"relative",height:420}}>
          <div style={{position:"absolute",top:30,left:0,width:240,borderRadius:18,overflow:"hidden",transform:"rotate(-5deg)",border:"3px solid #FFD4A8",boxShadow:"0 16px 50px rgba(0,0,0,.1)",background:"#fff",zIndex:1}}>
            <div style={{height:220,background:"linear-gradient(135deg,#FFF5EB,#FFE8D6)",display:"flex",flexDirection:"column",alignItems:"center",justifyContent:"center",position:"relative"}}>
              <div style={{fontSize:56}}>📷</div>
            </div>
            <div style={{padding:"14px 16px",textAlign:"center"}}>
              <div style={{fontFamily:"'Baloo 2',cursive",fontSize:"1rem",color:"#E67E22",marginBottom:2}}>Ananya's School Photo</div>
              <div style={{fontSize:".78rem",color:"#999"}}>A regular photo of your child</div>
            </div>
            <div style={{padding:"8px",textAlign:"center",background:"#FFF5EB",fontFamily:"'Baloo 2',cursive",fontSize:".78rem",color:"#E67E22",fontWeight:700}}>Step 1: Upload Photo</div>
          </div>
          <div style={{position:"absolute",top:"50%",left:"48%",transform:"translate(-50%,-50%)",zIndex:5,width:64,height:64,borderRadius:"50%",background:`linear-gradient(135deg,${G},#FFD77A)`,display:"flex",alignItems:"center",justifyContent:"center",boxShadow:"0 6px 25px rgba(255,184,48,.4)",animation:"pulse 2s ease-in-out infinite",fontSize:22,color:"#fff",fontWeight:800}}>→</div>
          <div style={{position:"absolute",top:10,right:0,width:260,borderRadius:18,overflow:"hidden",transform:"rotate(3deg)",border:`3px solid ${G}`,boxShadow:`0 20px 55px rgba(74,31,184,.15)`,background:"#fff",zIndex:2}}>
            <div style={{height:260,background:`linear-gradient(135deg,#EDE7FF,#C4B5FD)`,display:"flex",flexDirection:"column",alignItems:"center",justifyContent:"center",padding:16,position:"relative"}}>
              <div style={{fontSize:48,marginBottom:6}}>👸</div>
              <div style={{fontFamily:"'Baloo 2',cursive",fontSize:"1.05rem",color:"#fff",textAlign:"center",textShadow:"0 2px 8px rgba(0,0,0,.2)",lineHeight:1.3}}>Princess Ananya<br/>& the Dragon!</div>
              <div style={{fontSize:".75rem",color:"rgba(255,255,255,.8)",marginTop:6}}>Her real face in every illustration</div>
            </div>
            <div style={{padding:"10px",textAlign:"center",background:`linear-gradient(135deg,${R},${L})`,fontFamily:"'Baloo 2',cursive",fontWeight:700,fontSize:".85rem",color:"#fff"}}>Her face is IN the book!</div>
          </div>
        </div>
        <div>
          <span style={{display:"inline-block",padding:"5px 18px",borderRadius:30,fontSize:".82rem",fontWeight:700,background:"#EDE7FF",color:R,marginBottom:14}}>🌈 The Pandora Magic</span>
          <h2 style={{fontFamily:"'Baloo 2',cursive",fontSize:"clamp(1.8rem,3vw,2.5rem)",color:D,marginBottom:16}}>Real Photo. <span style={{color:R}}>Real Magic.</span></h2>
          <p style={{fontSize:"1.02rem",color:"#555",lineHeight:1.8,marginBottom:16}}>This isn't clip-art or generic illustrations. We take your child's <strong>actual photograph</strong> and weave it into every page of the storybook. They see themselves — their real face — as the hero of an incredible adventure.</p>
          <div style={{background:"linear-gradient(135deg,#FFF3E0,#FFE0B2)",borderRadius:16,padding:"18px 22px",marginBottom:20,borderLeft:`4px solid ${G}`}}>
            <h4 style={{fontFamily:"'Baloo 2',cursive",fontSize:"1.05rem",color:"#E67E22",marginBottom:4}}>📷 How the Photo Works</h4>
            <p style={{fontSize:".88rem",color:"#777",margin:0}}>Upload any clear photo of your child. Our artists blend their real face into hand-crafted storybook illustrations.</p>
          </div>
          <p style={{fontFamily:"'Caveat',cursive",fontSize:"1.45rem",color:"#FF6B6B",transform:"rotate(-2deg)",display:"inline-block",margin:"10px 0"}}>"Mommy, that's REALLY ME in the book!" 💜</p>
          <p style={{fontSize:".98rem",color:"#666",lineHeight:1.7,marginBottom:20}}>For coloring books, we transform their photo into beautiful line art they can color themselves!</p>
          <Btn onClick={()=>go("products")}>Create Their Book ✨</Btn>
        </div>
      </div>
    </section>

    <section style={{padding:"80px 20px",background:"linear-gradient(180deg,#fff,#FFF5EB)"}}>
      <div style={{textAlign:"center",marginBottom:50}}>
        <h2 style={{fontFamily:"'Baloo 2',cursive",fontSize:"clamp(2rem,4vw,2.8rem)",color:D,marginBottom:8}}><span style={{color:G}}>{collectionsData.length}</span> Magical Collections</h2>
        <p style={{color:"#888",fontSize:"1.02rem"}}>Every child. Every interest. Every dream.</p>
      </div>
      {collectionsData.length>0 ? (
        <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fill,minmax(310px,1fr))",gap:28,maxWidth:1180,margin:"0 auto"}}>
          {collectionsData.map(c=><Card3D key={c.id} c={c}/>)}
        </div>
      ) : (
        <div style={{maxWidth:1180,margin:"0 auto",textAlign:"center",padding:"24px 0",color:"#777",fontWeight:600}}>No collections available in database.</div>
      )}
      <div style={{textAlign:"center",marginTop:36}}>
        <Btn onClick={()=>go("collections")}>See All Collections →</Btn>
      </div>
    </section>

    <section id="refer" style={{background:"linear-gradient(180deg,#1A0A3E,#150F2D)",padding:"80px 20px"}}>
      <div style={{textAlign:"center",marginBottom:36}}>
        <div style={{fontSize:44,marginBottom:10}}>🎁</div>
        <h2 style={{fontFamily:"'Baloo 2',cursive",fontSize:"clamp(1.8rem,3vw,2.4rem)",color:"#fff",marginBottom:6}}>Share & <span style={{color:G}}>Earn Free Books</span></h2>
        <p style={{color:"rgba(255,255,255,.45)",fontSize:".95rem",maxWidth:480,margin:"0 auto"}}>Love PandoraPages? Share your unique code — when your friends buy, you earn free books.</p>
      </div>
      <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fit,minmax(230px,1fr))",gap:14,maxWidth:860,margin:"0 auto 36px"}}>
        {[["🔗","Share Your Code","Share your unique referral link with parents & friends"],["🛒","They Buy","When your referral makes a purchase, it's counted automatically"],["🎁","You Earn","Get free books delivered — the more you refer, the more you earn!"]].map(([ic,t,d],i)=><div key={i} style={{background:"rgba(255,255,255,.04)",borderRadius:16,padding:"26px 18px",textAlign:"center",border:"1px solid rgba(255,255,255,.06)"}}>
          <div style={{fontSize:28,marginBottom:4}}>{ic}</div><div style={{fontSize:".68rem",color:"rgba(255,255,255,.25)",fontWeight:700,letterSpacing:1,marginBottom:4}}>STEP {i+1}</div><h4 style={{fontFamily:"'Baloo 2',cursive",fontSize:"1.05rem",color:"#fff",marginBottom:4}}>{t}</h4><p style={{fontSize:".8rem",color:"rgba(255,255,255,.35)"}}>{d}</p>
        </div>)}
      </div>
      <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fit,minmax(280px,1fr))",gap:14,maxWidth:860,margin:"0 auto 36px"}}>
        <div style={{background:`${G}08`,borderRadius:18,padding:"24px 22px",border:`1px solid ${G}22`,textAlign:"left"}}>
          <div style={{fontSize:24,marginBottom:8}}>🏆</div>
          <h3 style={{fontFamily:"'Baloo 2',cursive",fontSize:"1.15rem",color:G,marginBottom:8}}>Refer 5 Buyers</h3>
          <p style={{fontSize:".85rem",color:"rgba(255,255,255,.55)",marginBottom:10}}>Earn 1 FREE digital book</p>
          <div style={{height:8,background:"rgba(255,255,255,.12)",borderRadius:999,overflow:"hidden",marginBottom:8}}>
            <div style={{height:"100%",width:`${(progressToFive/5)*100}%`,background:`linear-gradient(90deg,${G},#FFC947)`}} />
          </div>
          <div style={{fontSize:".8rem",color:hasFiveReward?"#7CFFB2":"rgba(255,255,255,.65)",fontWeight:700}}>
            {progressToFive}/5 referrals {hasFiveReward?"• Reward unlocked ✅":""}
          </div>
        </div>
        <div style={{background:`${L}0F`,borderRadius:18,padding:"24px 22px",border:`1px solid ${L}33`,textAlign:"left"}}>
          <div style={{fontSize:24,marginBottom:8}}>🚀</div>
          <h3 style={{fontFamily:"'Baloo 2',cursive",fontSize:"1.15rem",color:L,marginBottom:8}}>Refer 10 Buyers</h3>
          <p style={{fontSize:".85rem",color:"rgba(255,255,255,.55)",marginBottom:10}}>Earn FREE personalized digital book</p>
          <div style={{height:8,background:"rgba(255,255,255,.12)",borderRadius:999,overflow:"hidden",marginBottom:8}}>
            <div style={{height:"100%",width:`${(progressToTen/10)*100}%`,background:`linear-gradient(90deg,${L},#C4B5FD)`}} />
          </div>
          <div style={{fontSize:".8rem",color:hasTenReward?"#7CFFB2":"rgba(255,255,255,.65)",fontWeight:700}}>
            {progressToTen}/10 referrals {hasTenReward?"• Reward unlocked ✅":""}
          </div>
        </div>
      </div>
      <div style={{maxWidth:860,margin:"0 auto",background:"rgba(255,255,255,.04)",borderRadius:18,padding:"26px 28px",border:"1px solid rgba(255,255,255,.06)",display:"flex",alignItems:"center",justifyContent:"space-between",flexWrap:"wrap",gap:16}}>
        <div><div style={{fontSize:".68rem",color:"rgba(255,255,255,.25)",fontWeight:700,letterSpacing:2,marginBottom:4}}>YOUR REFERRAL CODE</div><div style={{fontFamily:"'Baloo 2',cursive",fontSize:"1.7rem",color:"#fff",letterSpacing:4}}>{profile?.referral_code||"SIGN IN"}</div><p style={{fontSize:".78rem",color:"rgba(255,255,255,.3)",marginTop:4}}>{profile?`${referrals}/10 referrals · ${Math.max(0,10-referrals)} more to max reward`:"Sign in to get your unique code"}</p></div>
        <div style={{display:"flex",flexDirection:"column",gap:10}}>
          <Btn bg={`linear-gradient(135deg,${G},#FFC947)`} c={D} onClick={()=>{navigator.clipboard?.writeText(`https://pandorapages.in/?ref=${profile?.referral_code||""}`);alert("Copied!")}} s={{padding:"10px 22px",fontSize:".88rem",color:D}}>📋 Copy Referral Link</Btn>
          <Btn bg={W} onClick={()=>window.open(`https://wa.me/?text=Hey!+Check+PandoraPages+-+kids+books+from+₹99!+Code+${profile?.referral_code||""}+📖+pandorapages.in`,"_blank")} s={{padding:"10px 22px",fontSize:".88rem"}}>💬 Share on WhatsApp</Btn>
        </div>
      </div>
    </section>

    <section style={{padding:"70px 20px",background:"linear-gradient(135deg,#E8F5E9,#C8E6C9,#A5D6A7)",textAlign:"center"}}>
      <h2 style={{fontFamily:"'Baloo 2',cursive",fontSize:"clamp(1.6rem,3vw,2.2rem)",color:"#1B5E20",marginBottom:10}}>🟢 Join Our WhatsApp Community</h2>
      <p style={{color:"#2E7D32",fontSize:"1rem",marginBottom:28}}>Weekly FREE coloring pages, story prompts & exclusive deals!</p>
      <a href="https://chat.whatsapp.com/CMevldqAxQEAP0z40jTF5j" target="_blank" rel="noreferrer" style={{display:"inline-flex",alignItems:"center",gap:8,background:W,color:"#fff",padding:"16px 40px",borderRadius:50,fontFamily:"'Baloo 2',cursive",fontSize:"1.1rem",fontWeight:700,textDecoration:"none",animation:"glow 2s ease-in-out infinite"}}>💬 Join 2,000+ Parents — FREE</a>
    </section>

    <section style={{padding:"70px 20px",background:C}}>
      <div style={{textAlign:"center",marginBottom:36}}><h2 style={{fontFamily:"'Baloo 2',cursive",fontSize:"clamp(1.6rem,3vw,2.2rem)",color:D}}>💬 What Families Say</h2></div>
      <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fit,minmax(280px,1fr))",gap:18,maxWidth:960,margin:"0 auto"}}>
        {[["My daughter saw herself as a princess and screamed with joy. Best ₹399 ever!","Priya M.","Mom of 5-yr-old"],["Started with ₹99 digital, then got the personalized coloring book. My son colors 'himself' every evening!","Rahul K.","Dad of 7-yr-old"],["The LifeReady emotions workbook helped my daughter express feelings. She asks for workbook time instead of screen time!","Sneha T.","Mom of 6-yr-old"]].map(([q,a,r],i)=><div key={i} style={{background:"#fff",borderRadius:18,padding:"22px",boxShadow:"0 3px 16px rgba(0,0,0,.04)"}}>
          <div style={{color:G,fontSize:"1rem",marginBottom:8}}>⭐⭐⭐⭐⭐</div><p style={{fontSize:".9rem",color:"#555",lineHeight:1.7,marginBottom:12,fontStyle:"italic"}}>"{q}"</p><div style={{fontWeight:700,fontSize:".85rem",color:D}}>{a} <span style={{color:"#999",fontWeight:500}}>— {r}</span></div>
        </div>)}
      </div>
    </section>

    <footer style={{background:D,color:"rgba(255,255,255,.55)",padding:"50px 28px 24px",textAlign:"center"}}>
      <h4 style={{fontFamily:"'Baloo 2',cursive",color:"#fff",fontSize:"1.1rem",marginBottom:10}}>Pandora Pages</h4>
      <p style={{fontSize:".82rem",lineHeight:1.7,maxWidth:560,margin:"0 auto"}}>Where every child becomes the hero. 10 collections, personalized books with real photos, and a mission to make reading magical.</p>
      <p style={{marginTop:14,fontSize:".78rem"}}>© 2026 Pandora Pages</p>
    </footer>
  </div>;

  const Store=()=><div style={{background:C,minHeight:"100vh",paddingTop:70}}>
    <div style={{background:`linear-gradient(135deg,${R},#6C5CE7,${L})`,padding:"50px 24px 70px",position:"relative",overflow:"hidden",textAlign:"center"}}>
      <span style={{background:"rgba(255,255,255,.12)",padding:"4px 14px",borderRadius:20,fontSize:".75rem",fontWeight:700,color:"#fff",letterSpacing:1}}>✨ COLLECTIONS</span>
      <h1 style={{fontFamily:"'Baloo 2',cursive",fontSize:"clamp(1.8rem,4vw,2.6rem)",color:"#fff",margin:"12px 0 6px"}}>{collectionsCountLabel}</h1>
      <p style={{color:"rgba(255,255,255,.7)",fontSize:"1rem",maxWidth:500,margin:"0 auto"}}>Every child. Every interest. Every dream. From ₹99.</p>
      <svg style={{position:"absolute",bottom:-1,left:0,right:0}} viewBox="0 0 1440 50" fill="none"><path d="M0 50V20C360 50 720 0 1080 20C1260 30 1380 45 1440 50H0Z" fill={C}/></svg>
    </div>
    <div style={{maxWidth:1180,margin:"0 auto",padding:"50px 20px 90px"}}>
      {collectionsData.length>0 ? (
        <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fill,minmax(310px,1fr))",gap:28}}>
          {collectionsData.map(c=><Card3D key={c.id} c={c}/>)}
        </div>
      ) : (
        <div style={{textAlign:"center",padding:"24px 0",color:"#777",fontWeight:600}}>No collections available in database.</div>
      )}
    </div>
  </div>;

  const Products=()=>{
    const items=[
      {emoji:"📱",title:"Digital Books",badge:"📚 Ready-Made Catalog",badgeBg:"linear-gradient(135deg,#27AE60,#2ECC71)",desc:"10 magical collections — stories, STEM, art, life skills & more. Instant digital delivery to your inbox or WhatsApp!",price:"₹99",pl:"per book onwards",cta:"Browse Collections",action:()=>go("collections"),hdr:"linear-gradient(135deg,#E8F5E9,#C8E6C9)",tag:"🔥 From ₹99",tagBg:"#FF6B6B",tagC:"#fff",feats:["Instant delivery","40+ titles","Ages 2–15"]},
      {emoji:"🎨",title:"Coloring Books",badge:"📷 Personalized",badgeBg:`linear-gradient(135deg,${R},${L})`,desc:"10 personalized coloring pages featuring your child's real photo as line art. Printed & shipped to your doorstep!",price:"₹199",pl:"printed & shipped",cta:"Create Coloring Book",action:()=>go("collection",COLLECTIONS[1]),hdr:"linear-gradient(135deg,#FFF3E0,#FFECB3)",tag:"📷 Personalized",tagBg:G,tagC:D,feats:["Real photo as line art","10 themed pages","Free preview first"]},
      {emoji:"📖",title:"Story Books",badge:"📷 Personalized + Real Photo",badgeBg:`linear-gradient(135deg,${R},${L})`,desc:"Your child's real photo inside a fully illustrated storybook — they become the hero of an unforgettable adventure!",price:"₹399",pl:"printed & shipped",cta:"Create Story Book",action:()=>go("collection",COLLECTIONS[0]),hdr:"linear-gradient(135deg,#EDE7FF,#F3E8FF)",tag:"⭐ Premium",tagBg:R,tagC:"#fff",feats:["Hardcover printed","Real face on every page","24–32 illustrated pages"]},
    ];
    return <div style={{background:C,minHeight:"100vh",paddingTop:70}}>
      <div style={{background:`linear-gradient(135deg,${R},#6C5CE7,${L})`,padding:"50px 24px 70px",position:"relative",overflow:"hidden",textAlign:"center"}}>
        <span style={{background:"rgba(255,255,255,.12)",padding:"4px 14px",borderRadius:20,fontSize:".75rem",fontWeight:700,color:"#fff",letterSpacing:1}}>📚 OUR PRODUCTS</span>
        <h1 style={{fontFamily:"'Baloo 2',cursive",fontSize:"clamp(1.8rem,4vw,2.6rem)",color:"#fff",margin:"12px 0 6px"}}>Choose What's Right for Your Child</h1>
        <p style={{color:"rgba(255,255,255,.75)",fontSize:"1rem",maxWidth:540,margin:"0 auto"}}>Three magical formats. From instant digital books at ₹99 to premium personalized story books with your child's real photo.</p>
        <svg style={{position:"absolute",bottom:-1,left:0,right:0}} viewBox="0 0 1440 50" fill="none"><path d="M0 50V20C360 50 720 0 1080 20C1260 30 1380 45 1440 50H0Z" fill={C}/></svg>
      </div>
      <div style={{maxWidth:1100,margin:"0 auto",padding:"50px 20px 90px"}}>
        <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fit,minmax(300px,1fr))",gap:24}}>
          {items.map((p,i)=><div key={i} onClick={p.action} style={{background:"#fff",borderRadius:22,overflow:"hidden",boxShadow:"0 4px 20px rgba(0,0,0,.06)",transition:"all .4s",position:"relative",cursor:"pointer"}}
            onMouseEnter={e=>{e.currentTarget.style.transform="translateY(-10px)";e.currentTarget.style.boxShadow="0 24px 60px rgba(0,0,0,.12)"}}
            onMouseLeave={e=>{e.currentTarget.style.transform="translateY(0)";e.currentTarget.style.boxShadow="0 4px 20px rgba(0,0,0,.06)"}}>
            <div style={{padding:"40px 24px 28px",textAlign:"center",background:p.hdr,position:"relative"}}>
              <div style={{fontSize:"3.5rem",marginBottom:10}}>{p.emoji}</div>
              <div style={{display:"inline-flex",padding:"3px 12px",borderRadius:20,fontSize:".72rem",fontWeight:700,background:p.badgeBg,color:"#fff",marginBottom:10}}>{p.badge}</div>
              <h3 style={{fontFamily:"'Baloo 2',cursive",fontSize:"1.45rem"}}>{p.title}</h3>
              <span style={{position:"absolute",top:14,right:14,background:p.tagBg,color:p.tagC,padding:"3px 10px",borderRadius:20,fontSize:".7rem",fontWeight:700}}>{p.tag}</span>
            </div>
            <div style={{padding:"22px 26px 28px"}}>
              <p style={{fontSize:".92rem",color:"#666",lineHeight:1.7,marginBottom:14}}>{p.desc}</p>
              <ul style={{listStyle:"none",padding:0,margin:"0 0 18px"}}>{p.feats.map(f=><li key={f} style={{fontSize:".85rem",color:"#555",padding:"5px 0",display:"flex",alignItems:"center",gap:8}}><span style={{color:"#27AE60",fontWeight:800}}>✓</span>{f}</li>)}</ul>
              <div style={{display:"flex",alignItems:"baseline",gap:6,marginBottom:16}}><span style={{fontFamily:"'Baloo 2',cursive",fontSize:"2rem",fontWeight:800,color:R}}>{p.price}</span><span style={{fontSize:".82rem",color:"#999"}}>{p.pl}</span></div>
              <Btn s={{width:"100%",justifyContent:"center",fontSize:".95rem",padding:"12px"}}>{p.cta} →</Btn>
            </div>
          </div>)}
        </div>
      </div>
    </div>;
  };

  const Collection=()=>{
    if(!col) return null;
    const genreMap={
      rootstales:["moral","bedtime","fantasy"],
      skillsprint:["educational","adventure"],
      moneyminds:["educational"],
      buildbrain:["educational"],
      artvault:["comedy","adventure"],
      kidsceo:["educational"],
      lifeready:["moral","educational"],
      lifepath:["adventure","comedy"],
    };
    const isP=col.personalized;
    const staticBooks=BOOKS[col.id]||[];
    const selectedCollectionId = String(col.id ?? "");
    const selectedCollectionName = String(col.name ?? "").trim().toLowerCase();
    const fromApi=digitalBooks
      .filter(b=>{
        const categoryId = b.category_id ?? b.category;
        const bookCategoryName = String(b.category_name ?? "").trim().toLowerCase();
        return String(categoryId)===selectedCollectionId
          || (selectedCollectionName !== "" && bookCategoryName === selectedCollectionName)
          || genreMap[col.id]?.includes((b.genre_name||"").toLowerCase());
      })
      .map(b=>({
        id:b.id,
        title:b.title,
        price:b.price,
        age:b.age || "All ages",
        pages:b.pages,
        style:b.style || "Standard",
        emoji:b.emoji||"📘",
        rat:b.rat,
        rev:b.rev,
        desc:b.desc,
        tags:parseTags(b.book_tags?.length?b.book_tags:b.book_tag),
        category_id:b.category_id,
        cover_image_url:b.cover_image_presigned_url || b.cover_image_url || null,
        front_image_url:b.front_image_presigned_url || b.front_image_url || b.cover_image_presigned_url || b.cover_image_url || null,
        back_image_url:b.back_image_presigned_url || b.back_image_url || null,
      }));
    const bks=(fromApi.length>0?fromApi:staticBooks).slice(0,1);
    return <div style={{background:C,minHeight:"100vh",paddingTop:70}}>
      <div style={{background:col.grad,padding:"40px 24px 60px",position:"relative",overflow:"hidden"}}>
        <div onClick={()=>go("collections")} style={{display:"inline-flex",alignItems:"center",gap:6,cursor:"pointer",color:"rgba(255,255,255,.7)",fontSize:".88rem",fontWeight:600,marginBottom:14}}>← Back to Collections</div>
        <div style={{display:"flex",alignItems:"center",gap:14,marginBottom:8}}>
          <div style={{width:52,height:52,borderRadius:16,background:"rgba(255,255,255,.15)",display:"flex",alignItems:"center",justifyContent:"center",fontSize:28}}>{col.emoji}</div>
          <div>
            <h1 style={{fontFamily:"'Baloo 2',cursive",fontSize:"clamp(1.6rem,3vw,2.3rem)",color:"#fff",margin:0}}>{col.name}</h1>
            {col.tags?.length>0&&<div style={{display:"flex",gap:6,flexWrap:"wrap",marginTop:6}}>{col.tags.map((tag)=><span key={tag} style={{color:"rgba(255,255,255,.95)",fontSize:".7rem",fontWeight:700,background:"rgba(255,255,255,.2)",padding:"3px 9px",borderRadius:999}}>{tag}</span>)}</div>}
          </div>
        </div>
        <p style={{color:"rgba(255,255,255,.8)",fontSize:".92rem",maxWidth:580,lineHeight:1.6}}>{col.desc}</p>
        {isP&&<div style={{display:"inline-flex",alignItems:"center",gap:6,background:"rgba(255,255,255,.15)",padding:"6px 16px",borderRadius:30,marginTop:12,fontSize:".82rem",color:"#fff",fontWeight:600}}>📷 Personalized with your child's real photo</div>}
        <svg style={{position:"absolute",bottom:-1,left:0,right:0}} viewBox="0 0 1440 50" fill="none"><path d="M0 50V20C360 50 720 0 1080 20C1260 30 1380 45 1440 50H0Z" fill={C}/></svg>
      </div>
      {isP&&<div style={{maxWidth:900,margin:"0 auto",padding:"28px 20px 0"}}>
        <div style={{background:"linear-gradient(135deg,#FFF3E0,#FFE0B2)",borderRadius:16,padding:"18px 22px",borderLeft:`4px solid ${G}`}}>
          <h4 style={{fontFamily:"'Baloo 2',cursive",fontSize:"1rem",color:"#E67E22",marginBottom:4}}>📷 How it works</h4>
          <p style={{fontSize:".88rem",color:"#777",margin:0}}>1. Pick a book template → 2. Upload your child's details & photo → 3. We send a free preview on WhatsApp → 4. Love it? Pay & we print + ship!</p>
        </div>
      </div>}
      <div style={{maxWidth:1100,margin:"0 auto",padding:"40px 20px 90px"}}>
        {(digitalBooksLoading) ? (
          <div style={{textAlign:"center",padding:"40px 0",color:"#777",fontWeight:600}}>Loading books from backend...</div>
        ) : (digitalBooksError) ? (
          <div style={{textAlign:"center",padding:"40px 0",color:"#C0392B",fontWeight:600}}>{digitalBooksError}</div>
        ) : (bks.length===0) ? (
          <div style={{textAlign:"center",padding:"40px 0",color:"#777",fontWeight:600}}>No books available for this category from backend yet. (Collection ID: {String(col.id)})</div>
        ) : (
          <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fill,minmax(250px,1fr))",gap:28}}>
            {bks.map(b=><BookCard3D key={b.id} b={b} col={col} isP={isP||b.is_personalized} onClick={()=>{if(b.is_personalized){setPersonalizeBook({...b,collection:col})}else if(isP){setPModal({book:b,collection:col})}else setBook({...b,collection:col})}}/>)}
          </div>
        )}
      </div>
    </div>;
  };

  const PreviewBtn=({book:b})=>{
    const [pvLoading,setPvLoading]=useState(false);
    const [pvErr,setPvErr]=useState("");
    const handlePreview=async()=>{
      setPvLoading(true);setPvErr("");
      try{
        const {url}=await getDigitalBookPreview(b.id);
        window.open(url,"_blank");
      }catch(e){setPvErr(e?.message||"Preview unavailable");}
      finally{setPvLoading(false);}
    };
    if(!b.pdf_url&&!b.is_personalized) return null;
    return <>
      {pvErr&&<div style={{fontSize:".75rem",color:"#C0392B",fontWeight:700,textAlign:"right"}}>{pvErr}</div>}
      <button onClick={handlePreview} disabled={pvLoading} style={{background:"transparent",border:`2px solid ${R}`,color:R,borderRadius:12,padding:"9px 20px",fontFamily:"'Baloo 2',cursive",fontWeight:800,fontSize:".9rem",cursor:"pointer",opacity:pvLoading?.6:1}}>{pvLoading?"⏳ Loading…":"👁️ Preview PDF"}</button>
    </>;
  };

  const PersonalizeModal=({book:b,onClose})=>{
    const [form,setForm]=useState({child_name:"",child_age:"",child_gender:"",parent_email:"",whatsapp_number:""});
    const [photos,setPhotos]=useState([]);
    const [loading,setLoading]=useState(false);
    const [error,setError]=useState("");
    const [success,setSuccess]=useState(false);
    const inputS={width:"100%",padding:"10px 14px",borderRadius:12,border:"2px solid #E8E0F0",fontSize:14,fontFamily:"inherit",outline:"none",boxSizing:"border-box"};
    const handleSubmit=async()=>{
      if(!form.child_name.trim()||!form.child_age||!form.child_gender||!form.parent_email.trim()){setError("Please fill all required fields.");return;}
      if(photos.length===0){setError("Please upload at least one photo.");return;}
      setLoading(true);setError("");
      try{
        await initiatePersonalizedBookOrder({
          child_name:form.child_name.trim(),
          child_age:Number(form.child_age),
          child_gender:form.child_gender,
          parent_email:form.parent_email.trim(),
          whatsapp_number:form.whatsapp_number.trim()||undefined,
          photos:Array.from(photos),
        });
        setSuccess(true);
      }catch(e){setError(e?.message||"Something went wrong. Please try again.");}
      finally{setLoading(false);}
    };
    return <div onClick={onClose} style={{position:"fixed",inset:0,background:"rgba(0,0,0,.55)",backdropFilter:"blur(8px)",zIndex:1005,display:"flex",alignItems:"center",justifyContent:"center",padding:16,animation:"fadeIn .3s"}}>
      <div onClick={e=>e.stopPropagation()} style={{background:"#fff",borderRadius:24,maxWidth:500,width:"100%",maxHeight:"92vh",overflow:"auto",animation:"slideUp .4s cubic-bezier(.4,0,.2,1)"}}>
        <div style={{background:`linear-gradient(135deg,${R},#6C5CE7)`,padding:"22px 24px 24px",position:"relative",borderRadius:"24px 24px 0 0"}}>
          <button onClick={onClose} style={{position:"absolute",top:12,right:12,width:28,height:28,borderRadius:"50%",border:"none",background:"rgba(255,255,255,.18)",color:"#fff",cursor:"pointer",fontSize:13}}>✕</button>
          <div style={{fontSize:".68rem",fontWeight:700,color:"rgba(255,255,255,.6)",letterSpacing:1,marginBottom:4}}>PERSONALIZE YOUR BOOK</div>
          <div style={{fontFamily:"'Baloo 2',cursive",fontSize:"1.2rem",color:"#fff",fontWeight:800}}>{b.title}</div>
        </div>
        {success ? (
          <div style={{padding:"40px 28px",textAlign:"center"}}>
            <div style={{fontSize:56,marginBottom:10}}>🎉</div>
            <h2 style={{fontFamily:"'Baloo 2',cursive",fontSize:"1.4rem",color:"#1A0A3E",marginBottom:8}}>Order Received!</h2>
            <p style={{color:"#555",fontSize:".9rem",lineHeight:1.7}}>We've received your personalized book order and photos. Our team will process it and reach out to you at <strong>{form.parent_email}</strong> shortly.</p>
            <button onClick={onClose} style={{marginTop:20,background:R,color:"#fff",border:"none",borderRadius:12,padding:"12px 28px",fontFamily:"'Baloo 2',cursive",fontWeight:800,fontSize:"1rem",cursor:"pointer"}}>Close</button>
          </div>
        ) : (
          <div style={{padding:"24px 24px 28px",display:"grid",gap:14}}>
            <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:12}}>
              <div style={{display:"grid",gap:4}}>
                <label style={{fontSize:".75rem",fontWeight:700,color:"#666",textTransform:"uppercase",letterSpacing:.5}}>Child's Name <span style={{color:"#b00020"}}>*</span></label>
                <input style={inputS} value={form.child_name} onChange={e=>setForm(s=>({...s,child_name:e.target.value}))} placeholder="E.g. Arjun" />
              </div>
              <div style={{display:"grid",gap:4}}>
                <label style={{fontSize:".75rem",fontWeight:700,color:"#666",textTransform:"uppercase",letterSpacing:.5}}>Age <span style={{color:"#b00020"}}>*</span></label>
                <input style={inputS} type="number" min={1} max={18} value={form.child_age} onChange={e=>setForm(s=>({...s,child_age:e.target.value}))} placeholder="E.g. 6" />
              </div>
            </div>
            <div style={{display:"grid",gap:4}}>
              <label style={{fontSize:".75rem",fontWeight:700,color:"#666",textTransform:"uppercase",letterSpacing:.5}}>Gender <span style={{color:"#b00020"}}>*</span></label>
              <select style={inputS} value={form.child_gender} onChange={e=>setForm(s=>({...s,child_gender:e.target.value}))}>
                <option value="">Select gender</option>
                <option value="male">Boy</option>
                <option value="female">Girl</option>
                <option value="other">Other</option>
              </select>
            </div>
            <div style={{display:"grid",gap:4}}>
              <label style={{fontSize:".75rem",fontWeight:700,color:"#666",textTransform:"uppercase",letterSpacing:.5}}>Parent Email <span style={{color:"#b00020"}}>*</span></label>
              <input style={inputS} type="email" value={form.parent_email} onChange={e=>setForm(s=>({...s,parent_email:e.target.value}))} placeholder="your@email.com" />
            </div>
            <div style={{display:"grid",gap:4}}>
              <label style={{fontSize:".75rem",fontWeight:700,color:"#666",textTransform:"uppercase",letterSpacing:.5}}>WhatsApp Number <span style={{color:"#aaa"}}>(optional)</span></label>
              <input style={inputS} value={form.whatsapp_number} onChange={e=>setForm(s=>({...s,whatsapp_number:e.target.value}))} placeholder="+91 98765 43210" />
            </div>
            <div style={{display:"grid",gap:4}}>
              <label style={{fontSize:".75rem",fontWeight:700,color:"#666",textTransform:"uppercase",letterSpacing:.5}}>Child's Photos <span style={{color:"#b00020"}}>*</span></label>
              <input type="file" accept="image/*" multiple style={{...inputS,padding:"8px 14px"}} onChange={e=>setPhotos(e.target.files)} />
              <div style={{fontSize:".75rem",color:"#999"}}>Upload clear face photos (JPEG/PNG). More photos = better personalization!</div>
            </div>
            {error&&<div style={{color:"#C0392B",fontSize:".82rem",fontWeight:700,background:"#FFF0F0",borderRadius:10,padding:"8px 12px"}}>{error}</div>}
            <button onClick={handleSubmit} disabled={loading} style={{background:loading?"#ccc":`linear-gradient(135deg,${R},#6C5CE7)`,color:"#fff",border:"none",borderRadius:14,padding:"14px",fontFamily:"'Baloo 2',cursive",fontWeight:800,fontSize:"1.05rem",cursor:loading?"not-allowed":"pointer",marginTop:4}}>{loading?"⏳ Submitting…":"🎨 Customize & Order"}</button>
          </div>
        )}
      </div>
    </div>;
  };

  const BookM=()=>{
    if(!book) return null;
    const b=book,c=b.collection;
    const frontCover = b.front_image_url || b.cover_image_url;
    const backCover = b.back_image_url;
    return <div onClick={()=>setBook(null)} style={{position:"fixed",inset:0,background:"rgba(0,0,0,.5)",backdropFilter:"blur(8px)",zIndex:1001,display:"flex",alignItems:"center",justifyContent:"center",padding:16,animation:"fadeIn .3s"}}>
      <div onClick={e=>e.stopPropagation()} style={{background:"#fff",borderRadius:24,maxWidth:540,width:"100%",maxHeight:"90vh",overflow:"auto",animation:"slideUp .4s cubic-bezier(.4,0,.2,1)"}}>
        <button onClick={()=>setBook(null)} style={{position:"sticky",top:12,float:"right",marginRight:12,width:32,height:32,borderRadius:"50%",border:"none",background:"rgba(0,0,0,.06)",cursor:"pointer",fontSize:16,zIndex:2}}>✕</button>
        <div style={{padding:"18px 18px 0",display:"grid",gridTemplateColumns:backCover?"1fr 1fr":"1fr",gap:12}}>
          <div style={{borderRadius:14,overflow:"hidden",background:`linear-gradient(135deg,${c.color}22,${c.color}55)`,height:180,display:"flex",alignItems:"center",justifyContent:"center",position:"relative"}}>
            {frontCover ? (
              <img src={frontCover} alt={`${b.title} front cover`} style={{width:"100%",height:"100%",objectFit:"cover"}} />
            ) : (
              <div style={{fontSize:62}}>{b.emoji}</div>
            )}
            <div style={{position:"absolute",left:10,bottom:10,background:"rgba(255,255,255,.92)",padding:"3px 10px",borderRadius:20,fontSize:".68rem",fontWeight:800,color:D}}>Front Cover</div>
          </div>
          {backCover && (
            <div style={{borderRadius:14,overflow:"hidden",background:`linear-gradient(135deg,${c.color}22,${c.color}55)`,height:180,display:"flex",alignItems:"center",justifyContent:"center",position:"relative"}}>
              <img src={backCover} alt={`${b.title} back cover`} style={{width:"100%",height:"100%",objectFit:"cover"}} />
              <div style={{position:"absolute",left:10,bottom:10,background:"rgba(255,255,255,.92)",padding:"3px 10px",borderRadius:20,fontSize:".68rem",fontWeight:800,color:D}}>Back Cover</div>
            </div>
          )}
        </div>
        <div style={{padding:"22px 26px 28px"}}>
          <h2 style={{fontFamily:"'Baloo 2',cursive",fontSize:"1.4rem",color:D,margin:"0 0 4px"}}>{b.title}</h2>
          <div style={{display:"flex",alignItems:"center",gap:6,marginBottom:12}}><Stars r={b.rat}/><span style={{fontSize:".85rem",fontWeight:700,color:"#444"}}>{b.rat}</span><span style={{fontSize:".8rem",color:"#aaa"}}>({b.rev} reviews)</span></div>
          <p style={{fontSize:".92rem",color:"#666",lineHeight:1.7,marginBottom:20}}>{b.desc}</p>
          {b.tags?.length>0&&<div style={{display:"flex",gap:6,flexWrap:"wrap",marginBottom:14}}>{b.tags.map((tag)=><span key={tag} style={{background:`${c.color}15`,color:c.color,padding:"3px 10px",borderRadius:999,fontSize:".7rem",fontWeight:700}}>{tag}</span>)}</div>}
          <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:10,marginBottom:22}}>
            {[["Collection",c.name,c.emoji],["Style",b.style || "Standard","🎨"],["Age",b.age || "All ages","👶"],["Pages",`${b.pages}${b.pages===1?" board":" pg"}`,"📄"]].map(([l,v,ic])=><div key={l} style={{background:"#F8F5FF",borderRadius:12,padding:"10px 14px",display:"flex",alignItems:"center",gap:8}}><span style={{fontSize:18}}>{ic}</span><div><div style={{fontSize:".68rem",color:"#bbb",fontWeight:600,textTransform:"uppercase"}}>{l}</div><div style={{fontSize:".85rem",fontWeight:700,color:"#333"}}>{v}</div></div></div>)}
          </div>
            <div style={{display:"flex",alignItems:"center",justifyContent:"space-between",background:"#F8F5FF",borderRadius:16,padding:"16px 20px"}}>
            <div><div style={{fontSize:".7rem",color:"#bbb"}}>PRICE</div><div style={{fontFamily:"'Baloo 2',cursive",fontSize:"2rem",fontWeight:800,color:R,lineHeight:1}}>₹{b.price}</div><div style={{fontSize:".72rem",color:"#bbb"}}>{b.is_personalized?"Custom order":"Instant delivery"}</div></div>
            <div style={{display:"flex",flexDirection:"column",gap:8,alignItems:"flex-end"}}>
              {b.is_personalized ? (
                <Btn onClick={()=>{setPersonalizeBook(b);setBook(null)}} s={{background:`linear-gradient(135deg,#6C5CE7,${R})`}}>🎨 Customize &amp; Order</Btn>
              ) : (
                <Btn onClick={()=>{setCk(b);setBook(null)}}>🛒 Buy Now</Btn>
              )}
              <PreviewBtn book={b} />
            </div>
          </div>
        </div>
      </div>
    </div>;
  };

  const CkM=()=>{
    if(!checkout) return null;
    const b=checkout;
    const taxableAmount = Number(b.price) || 0;
    const gstRatePercent = 18;
    const gstAmount = Number(((taxableAmount * gstRatePercent) / 100).toFixed(2));
    const totalAmount = Number((taxableAmount + gstAmount).toFixed(2));
    return <div onClick={resetCk} style={{position:"fixed",inset:0,background:"rgba(0,0,0,.5)",backdropFilter:"blur(8px)",zIndex:1002,display:"flex",alignItems:"center",justifyContent:"center",padding:16,animation:"fadeIn .3s"}}>
      <div onClick={e=>e.stopPropagation()} style={{background:"#fff",borderRadius:24,maxWidth:460,width:"100%",overflow:"hidden",animation:"slideUp .4s cubic-bezier(.4,0,.2,1)"}}>
        {!done?<>
          <div style={{background:`linear-gradient(135deg,${R},#6C5CE7)`,padding:"22px 22px 26px",position:"relative"}}><button onClick={resetCk} style={{position:"absolute",top:10,right:10,width:28,height:28,borderRadius:"50%",border:"none",background:"rgba(255,255,255,.15)",color:"#fff",cursor:"pointer",fontSize:13}}>✕</button><div style={{fontSize:".68rem",fontWeight:700,color:"rgba(255,255,255,.5)",letterSpacing:1,marginBottom:4}}>CHECKOUT</div><div style={{display:"flex",alignItems:"center",gap:10}}><div style={{width:44,height:44,borderRadius:12,background:"rgba(255,255,255,.12)",display:"flex",alignItems:"center",justifyContent:"center",fontSize:22}}>{b.emoji}</div><div><div style={{fontFamily:"'Baloo 2',cursive",fontSize:"1.05rem",color:"#fff"}}>{b.title}</div><div style={{fontSize:".78rem",color:"rgba(255,255,255,.6)"}}>{b.style || "Standard"} • {b.pages} pages</div></div></div></div>
          <div style={{padding:22}}>
            <div style={{marginBottom:18}}>
              <div style={{fontSize:".75rem",fontWeight:700,color:"#999",textTransform:"uppercase",letterSpacing:.5,marginBottom:8}}>📬 Delivery</div>
              <div style={{padding:"14px",borderRadius:14,border:`2px solid ${R}`,background:"#F8F5FF",textAlign:"center"}}>
                <div style={{fontSize:22,marginBottom:2}}>📧</div>
                <div style={{fontWeight:700,fontSize:".85rem",color:R}}>Email only</div>
              </div>
            </div>
            <div style={{marginBottom:18}}><label style={{fontSize:".75rem",fontWeight:700,color:"#999",textTransform:"uppercase",letterSpacing:.5,display:"block",marginBottom:5}}>📧 Email</label><input value={contact} onChange={e=>setContact(e.target.value)} placeholder="your@email.com" style={{width:"100%",padding:"11px 14px",borderRadius:12,border:"2px solid #E8E0F0",fontSize:14,fontFamily:"inherit",outline:"none"}}/></div>
            <div style={{background:"#F8F5FF",borderRadius:14,padding:"14px 16px",marginBottom:18}}>
              <div style={{display:"flex",justifyContent:"space-between",marginBottom:5}}><span style={{fontSize:".85rem",color:"#666"}}>{b.title}</span><span style={{fontSize:".85rem",fontWeight:700}}>₹{taxableAmount.toFixed(2)}</span></div>
              <div style={{display:"flex",justifyContent:"space-between",marginBottom:5}}><span style={{fontSize:".8rem",color:"#666"}}>GST ({gstRatePercent}%)</span><span style={{fontSize:".8rem",fontWeight:700}}>₹{gstAmount.toFixed(2)}</span></div>
              <div style={{borderTop:"1px dashed #D6C4FF",paddingTop:8,display:"flex",justifyContent:"space-between"}}><span style={{fontWeight:800}}>Total</span><span style={{fontFamily:"'Baloo 2',cursive",fontSize:"1.3rem",fontWeight:800,color:R}}>₹{totalAmount.toFixed(2)}</span></div>
            </div>
            {checkoutError && (
              <div style={{marginBottom:12,color:"#C0392B",fontSize:".82rem",fontWeight:700}}>{checkoutError}</div>
            )}
            <button onClick={async()=>{
              if(!contact.trim())return;
              if(!user){setAuthMode("signin");setAuthOpen(true);return}

              try{
                setCheckoutError("");
                const paymentOrder = await createDigitalPaymentOrder({
                  book_id:b.id,
                  delivery_method:"email",
                  delivery_contact:contact.trim(),
                });

                await loadRazorpaySdk();

                const rz = new window.Razorpay({
                  key: paymentOrder.key_id,
                  amount: paymentOrder.amount,
                  currency: paymentOrder.currency,
                  name: "Panda Tales",
                  description: b.title,
                  order_id: paymentOrder.razorpay_order_id,
                  prefill: {
                    email: contact.trim() || user.email,
                  },
                  notes: {
                    book_id: String(b.id),
                    delivery_method: "email",
                    delivery_contact: contact.trim(),
                  },
                  handler: async function (response) {
                    await verifyDigitalPayment({
                      razorpay_order_id: response.razorpay_order_id,
                      razorpay_payment_id: response.razorpay_payment_id,
                      razorpay_signature: response.razorpay_signature,
                    });
                    setDone(true);
                  },
                  modal: {
                    ondismiss: function () {
                      setCheckoutError("Payment was cancelled.");
                    },
                  },
                  theme: { color: "#4A1FB8" },
                });

                rz.open();
              }catch(e){
                setCheckoutError(e.message || "Payment failed. Please try again.");
              }
            }} style={{width:"100%",background:contact.trim()?`linear-gradient(135deg,${R},#6C5CE7)`:"#DDD",color:contact.trim()?"#fff":"#999",border:"none",padding:14,borderRadius:14,fontFamily:"'Baloo 2',cursive",fontSize:"1.05rem",fontWeight:700,cursor:contact.trim()?"pointer":"not-allowed"}}>💳 Pay ₹{totalAmount.toFixed(2)}</button>
          </div>
        </>:
        <div style={{padding:"48px 26px",textAlign:"center"}}><div style={{fontSize:56,marginBottom:10,animation:"popIn .6s cubic-bezier(.68,-.55,.265,1.55)"}}>🎉</div><h2 style={{fontFamily:"'Baloo 2',cursive",fontSize:"1.5rem",color:D,marginBottom:6}}>Order Placed!</h2><p style={{fontSize:".92rem",color:"#666",lineHeight:1.7,marginBottom:8}}><strong>{b.title}</strong> → <span style={{color:R,fontWeight:700}}>{contact}</span> via {del==="email"?"Email":"WhatsApp"}</p><p style={{fontSize:".84rem",color:"#666",lineHeight:1.6,marginBottom:18}}>Invoice has been sent to your registered email with GST breakup.</p><div style={{display:"flex",gap:10,justifyContent:"center",flexWrap:"wrap"}}><Btn onClick={()=>{resetCk();go("collections")}}>Browse More</Btn><Btn bg={W}>💬 Join Community</Btn></div></div>}
      </div>
    </div>;
  };

  const PM=()=>{
    if(!pModal) return null;
    const {book:b,collection:c}=pModal;
    const isStory=c.id==="talecraft";
    return <div onClick={resetP} style={{position:"fixed",inset:0,background:"rgba(0,0,0,.5)",backdropFilter:"blur(8px)",zIndex:1002,display:"flex",alignItems:"center",justifyContent:"center",padding:16,animation:"fadeIn .3s"}}>
      <div onClick={e=>e.stopPropagation()} style={{background:"#fff",borderRadius:24,maxWidth:520,width:"100%",maxHeight:"92vh",overflow:"auto",animation:"slideUp .4s cubic-bezier(.4,0,.2,1)"}}>
        {!pDone?<>
          <div style={{background:c.grad,padding:"24px 22px 30px",position:"relative",borderRadius:"24px 24px 0 0"}}>
            <button onClick={resetP} style={{position:"absolute",top:10,right:10,width:28,height:28,borderRadius:"50%",border:"none",background:"rgba(255,255,255,.15)",color:"#fff",cursor:"pointer",fontSize:13}}>✕</button>
            <div style={{display:"flex",alignItems:"center",gap:10,marginBottom:8}}>
              <div style={{fontSize:32}}>{b.emoji}</div>
              <div><div style={{fontFamily:"'Baloo 2',cursive",fontSize:"1.15rem",color:"#fff"}}>{b.title}</div><div style={{fontSize:".78rem",color:"rgba(255,255,255,.7)"}}>{isStory?"Personalized Story Book — ₹"+b.price:"Personalized Coloring Book — ₹"+b.price}</div></div>
            </div>
            <div style={{display:"flex",gap:5,marginTop:10}}>{[1,2,3].map(s=><div key={s} style={{flex:1,height:4,borderRadius:2,background:pStep>=s?"rgba(255,255,255,.6)":"rgba(255,255,255,.15)",transition:"all .3s"}}/>)}</div>
          </div>
          <div style={{padding:"22px 24px 26px"}}>
            {pStep===1&&<><h3 style={{fontFamily:"'Baloo 2',cursive",fontSize:"1.05rem",marginBottom:14,color:D}}>👶 Child's Details</h3>
              {[["Child's Name","name","Ananya, Arjun..."],["Age","age","e.g. 5"]].map(([l,k,ph])=><div key={k} style={{marginBottom:12}}><label style={{fontSize:".75rem",fontWeight:700,color:"#999",textTransform:"uppercase",letterSpacing:.5,display:"block",marginBottom:4}}>{l}</label><input value={pForm[k]} onChange={e=>setPF(p=>({...p,[k]:e.target.value}))} placeholder={ph} style={{width:"100%",padding:"11px 14px",borderRadius:12,border:"2px solid #E8E0F0",fontSize:14,fontFamily:"inherit",outline:"none"}}/></div>)}
              <div style={{marginBottom:12}}><label style={{fontSize:".75rem",fontWeight:700,color:"#999",textTransform:"uppercase",letterSpacing:.5,display:"block",marginBottom:4}}>Parent Email <span style={{color:"#b00020"}}>*</span></label><input type="email" value={pForm.email} onChange={e=>setPF(p=>({...p,email:e.target.value}))} placeholder="your@email.com" style={{width:"100%",padding:"11px 14px",borderRadius:12,border:"2px solid #E8E0F0",fontSize:14,fontFamily:"inherit",outline:"none"}}/></div>
              <div style={{marginBottom:14}}><label style={{fontSize:".75rem",fontWeight:700,color:"#999",textTransform:"uppercase",letterSpacing:.5,display:"block",marginBottom:4}}>Gender</label><div style={{display:"flex",gap:8}}>{["Girl 👧","Boy 👦","Other"].map(g=><div key={g} onClick={()=>setPF(p=>({...p,gender:g}))} style={{flex:1,padding:"10px",borderRadius:12,border:pForm.gender===g?`2px solid ${R}`:"2px solid #E8E0F0",background:pForm.gender===g?"#F8F5FF":"#fff",cursor:"pointer",textAlign:"center",fontWeight:600,fontSize:".85rem",color:pForm.gender===g?R:"#666"}}>{g}</div>)}</div></div>
              <Btn onClick={()=>{if(pForm.name&&pForm.age&&pForm.email)setPStep(2)}} s={{width:"100%",justifyContent:"center",opacity:(pForm.name&&pForm.age&&pForm.email)?1:.6}}>Next — Upload Photo →</Btn>
            </>}
            {pStep===2&&<><h3 style={{fontFamily:"'Baloo 2',cursive",fontSize:"1.05rem",marginBottom:14,color:D}}>📷 Upload Photo</h3>
              <label htmlFor="pUp" style={{display:"block",border:`2px dashed ${pForm.photoFile?"#A29BFE":"#D6C4FF"}`,borderRadius:18,padding:"28px 20px",textAlign:"center",background:pForm.photoFile?"#F3F0FF":"#FAFAFE",marginBottom:14,cursor:"pointer",transition:"all .25s"}}>
                {pForm.photoFile ? (
                  <div>
                    <img src={URL.createObjectURL(pForm.photoFile)} alt="Preview" style={{width:100,height:100,borderRadius:14,objectFit:"cover",border:`3px solid ${R}`,marginBottom:8}}/>
                    <p style={{fontWeight:800,color:R,margin:"4px 0 2px",fontSize:".9rem"}}>✅ Photo selected</p>
                    <p style={{fontSize:".75rem",color:"#888",margin:0}}>{pForm.photoFile.name}</p>
                    <span style={{display:"inline-block",marginTop:8,background:"#F8F5FF",color:R,padding:"5px 14px",borderRadius:30,fontWeight:700,fontSize:".8rem",border:`1px solid ${L}`}}>Change Photo</span>
                  </div>
                ) : (
                  <div>
                    <div style={{fontSize:44,marginBottom:6}}>📷</div>
                    <p style={{fontWeight:700,color:R,marginBottom:3}}>Click to upload</p>
                    <p style={{fontSize:".78rem",color:"#999",marginBottom:10}}>Clear face photo • JPG/PNG • Max 5MB</p>
                    <span style={{display:"inline-block",background:"#F8F5FF",color:R,padding:"7px 18px",borderRadius:30,fontWeight:700,fontSize:".85rem",border:`1px solid ${L}`}}>Choose Photo</span>
                  </div>
                )}
              </label>
              <input type="file" accept="image/*" style={{display:"none"}} id="pUp" onChange={e=>{const f=e.target.files?.[0];if(f)setPF(p=>({...p,photoFile:f}));}}/>
              <div style={{display:"flex",gap:8}}><button onClick={()=>setPStep(1)} style={{flex:1,padding:11,borderRadius:12,border:"2px solid #E8E0F0",background:"#fff",fontFamily:"inherit",fontWeight:700,cursor:"pointer",fontSize:".88rem",color:"#666"}}>← Back</button><Btn onClick={()=>{if(pForm.photoFile)setPStep(3)}} s={{flex:2,justifyContent:"center",opacity:pForm.photoFile?1:.5}}>Next — Choose Theme →</Btn></div>
            </>}
            {pStep===3&&<><h3 style={{fontFamily:"'Baloo 2',cursive",fontSize:"1.05rem",marginBottom:10,color:D}}>🎭 Choose Theme</h3>
              <div style={{display:"grid",gridTemplateColumns:"repeat(3,1fr)",gap:8,marginBottom:14}}>
                {["🏰 Adventure","👸 Princess","🚀 Space","🦕 Dinosaurs","🧚 Fantasy","🌊 Underwater","🦸 Superhero","🌴 Jungle","🙏 Mythology"].map(t=><div key={t} onClick={()=>setPF(p=>({...p,theme:t}))} style={{padding:"12px 6px",borderRadius:12,border:pForm.theme===t?`2px solid ${R}`:"2px solid #E8E0F0",background:pForm.theme===t?"#F8F5FF":"#fff",textAlign:"center",cursor:"pointer",fontSize:".8rem",fontWeight:600,color:pForm.theme===t?R:"#666"}}>{t}</div>)}
              </div>
              <div style={{marginBottom:12}}><label style={{fontSize:".75rem",fontWeight:700,color:"#999",textTransform:"uppercase",letterSpacing:.5,display:"block",marginBottom:4}}>📱 WhatsApp Number (for preview)</label><input value={pForm.phone} onChange={e=>setPF(p=>({...p,phone:e.target.value}))} placeholder="+91 98765 43210" style={{width:"100%",padding:"11px 14px",borderRadius:12,border:"2px solid #E8E0F0",fontSize:14,fontFamily:"inherit",outline:"none"}}/></div>
              {pError&&<div style={{marginBottom:10,color:"#C0392B",fontSize:".82rem",fontWeight:700,background:"#FFF0F0",borderRadius:10,padding:"8px 12px"}}>{pError}</div>}
              <div style={{display:"flex",gap:8}}><button onClick={()=>setPStep(2)} style={{flex:1,padding:11,borderRadius:12,border:"2px solid #E8E0F0",background:"#fff",fontFamily:"inherit",fontWeight:700,cursor:"pointer",fontSize:".88rem",color:"#666"}}>← Back</button><Btn bg={W} onClick={async()=>{
                if(!pForm.theme){setPError("Please choose a theme.");return;}
                const genderMap={"Girl 👧":"female","Boy 👦":"male","Other":"other"};
                setPSubmitting(true);setPError("");
                try{
                  await initiatePersonalizedBookOrder({
                    child_name:pForm.name,
                    child_age:Number(pForm.age),
                    child_gender:genderMap[pForm.gender]||"other",
                    parent_email:pForm.email,
                    whatsapp_number:pForm.phone||undefined,
                    selected_theme_name:pForm.theme||undefined,
                    photos:pForm.photoFile?[pForm.photoFile]:[],
                  });
                  setPDone(true);
                }catch(e){setPError(e?.message||"Something went wrong. Please try again.");}
                finally{setPSubmitting(false);}
              }} s={{flex:2,justifyContent:"center",opacity:pSubmitting?.6:1}}>{pSubmitting?"⏳ Submitting…":"📱 Get Free Preview"}</Btn></div>
            </>}
          </div>
        </>:
        <div style={{padding:"48px 26px",textAlign:"center"}}><div style={{fontSize:56,marginBottom:10,animation:"popIn .6s cubic-bezier(.68,-.55,.265,1.55)"}}>🎉</div><h2 style={{fontFamily:"'Baloo 2',cursive",fontSize:"1.4rem",color:D,marginBottom:6}}>Preview Coming Soon!</h2>
          <p style={{fontSize:".92rem",color:"#666",lineHeight:1.7,marginBottom:6}}>We're creating <strong>{pForm.name}</strong>'s personalized {isStory?"story":"coloring"} book!</p>
          <div style={{background:"#F0FFF0",borderRadius:14,padding:16,margin:"14px 0 20px",textAlign:"left"}}><p style={{fontSize:".85rem",color:"#2E7D32",marginBottom:6}}>📱 <strong>Check WhatsApp</strong> ({pForm.phone}) within 24 hours</p><p style={{fontSize:".82rem",color:"#555",margin:0}}>You'll get 2–3 preview pages. Reply "YES" to get the payment link!</p></div>
          <Btn onClick={resetP} s={{width:"100%",justifyContent:"center"}}>✨ Back to Browsing</Btn>
        </div>}
      </div>
    </div>;
  };

  const AuthM=()=>{
    if(!authOpen) return null;
    return <div onClick={()=>setAuthOpen(false)} style={{position:"fixed",inset:0,background:"rgba(0,0,0,.5)",backdropFilter:"blur(8px)",zIndex:1003,display:"flex",alignItems:"center",justifyContent:"center",padding:16,animation:"fadeIn .3s"}}>
      <div onClick={e=>e.stopPropagation()} style={{background:"#fff",borderRadius:24,maxWidth:420,width:"100%",overflow:"hidden",animation:"slideUp .4s cubic-bezier(.4,0,.2,1)"}}>
        <div style={{background:`linear-gradient(135deg,${R},#6C5CE7,${L})`,padding:"28px 24px 32px",position:"relative",textAlign:"center"}}>
          <button onClick={()=>setAuthOpen(false)} style={{position:"absolute",top:10,right:10,width:28,height:28,borderRadius:"50%",border:"none",background:"rgba(255,255,255,.15)",color:"#fff",cursor:"pointer",fontSize:13}}>✕</button>
          <div style={{fontSize:36,marginBottom:6}}>📖</div>
          <h2 style={{fontFamily:"'Baloo 2',cursive",fontSize:"1.3rem",color:"#fff",margin:0}}>{authMode==="signup"?"Join Pandora Pages":"Welcome Back"}</h2>
          <p style={{fontSize:".82rem",color:"rgba(255,255,255,.75)",marginTop:4}}>{authMode==="signup"?"Get your unique referral code":"Sign in to track orders & referrals"}</p>
        </div>
        <div style={{padding:24}}>
          {authMode==="signup"&&<div style={{marginBottom:12}}><label style={{fontSize:".72rem",fontWeight:700,color:"#999",textTransform:"uppercase",letterSpacing:.5,display:"block",marginBottom:4}}>Full Name</label><input value={authForm.fullName} onChange={e=>setAuthForm(f=>({...f,fullName:e.target.value}))} placeholder="Jane Doe" style={{width:"100%",padding:"11px 14px",borderRadius:12,border:"2px solid #E8E0F0",fontSize:14,fontFamily:"inherit",outline:"none"}}/></div>}
          {authMode==="signup"&&<div style={{marginBottom:12}}><label style={{fontSize:".72rem",fontWeight:700,color:"#999",textTransform:"uppercase",letterSpacing:.5,display:"block",marginBottom:4}}>Referral Code (optional)</label><input value={authForm.referralCode} onChange={e=>setAuthForm(f=>({...f,referralCode:e.target.value.toUpperCase()}))} placeholder="PPXXXXXX" style={{width:"100%",padding:"11px 14px",borderRadius:12,border:"2px solid #E8E0F0",fontSize:14,fontFamily:"inherit",outline:"none"}}/></div>}
          <div style={{marginBottom:12}}><label style={{fontSize:".72rem",fontWeight:700,color:"#999",textTransform:"uppercase",letterSpacing:.5,display:"block",marginBottom:4}}>Email</label><input type="email" value={authForm.email} onChange={e=>setAuthForm(f=>({...f,email:e.target.value}))} placeholder="you@email.com" style={{width:"100%",padding:"11px 14px",borderRadius:12,border:"2px solid #E8E0F0",fontSize:14,fontFamily:"inherit",outline:"none"}}/></div>
          <div style={{marginBottom:14}}><label style={{fontSize:".72rem",fontWeight:700,color:"#999",textTransform:"uppercase",letterSpacing:.5,display:"block",marginBottom:4}}>Password</label><input type="password" value={authForm.password} onChange={e=>setAuthForm(f=>({...f,password:e.target.value}))} placeholder="At least 8 characters" style={{width:"100%",padding:"11px 14px",borderRadius:12,border:"2px solid #E8E0F0",fontSize:14,fontFamily:"inherit",outline:"none"}}/></div>
          {authErr&&<div style={{background:"#FEE",color:"#C0392B",padding:"10px 14px",borderRadius:10,fontSize:".82rem",marginBottom:12}}>{authErr}</div>}
          <button onClick={submitAuth} disabled={authLoading||!authForm.email||!authForm.password} style={{width:"100%",background:authLoading||!authForm.email||!authForm.password?"#DDD":`linear-gradient(135deg,${R},#6C5CE7)`,color:authLoading||!authForm.email||!authForm.password?"#999":"#fff",border:"none",padding:14,borderRadius:14,fontFamily:"'Baloo 2',cursive",fontSize:"1.02rem",fontWeight:700,cursor:authLoading?"wait":"pointer",marginBottom:12}}>{authLoading?"...":authMode==="signup"?"✨ Create Account":"🔑 Sign In"}</button>
          <p style={{textAlign:"center",fontSize:".88rem",color:"#666"}}>{authMode==="signup"?"Already have an account? ":"New here? "}<span onClick={()=>{setAuthMode(authMode==="signup"?"signin":"signup");setAuthErr("")}} style={{color:R,fontWeight:700,cursor:"pointer"}}>{authMode==="signup"?"Sign In":"Create Account"}</span></p>
        </div>
      </div>
    </div>;
  };

  return <div>
    <style>{`@import url('https://fonts.googleapis.com/css2?family=Baloo+2:wght@400;500;600;700;800&family=Quicksand:wght@300;400;500;600;700&family=Caveat:wght@400;700&display=swap');*{margin:0;padding:0;box-sizing:border-box}html{scroll-behavior:smooth}body{font-family:'Quicksand',sans-serif;overflow-x:hidden}@keyframes fadeIn{from{opacity:0}to{opacity:1}}@keyframes slideUp{from{opacity:0;transform:translateY(40px) scale(.96)}to{opacity:1;transform:translateY(0) scale(1)}}@keyframes popIn{0%{transform:scale(0)}60%{transform:scale(1.15)}100%{transform:scale(1)}}@keyframes float{0%,100%{transform:translateY(0)}50%{transform:translateY(-12px)}}@keyframes shimmer{0%{background-position:200% 0}100%{background-position:-200% 0}}@keyframes pulse{0%,100%{transform:scale(1)}50%{transform:scale(1.08)}}@keyframes waBounce{0%,100%{transform:translateY(0)}50%{transform:translateY(-8px)}}@keyframes glow{0%,100%{box-shadow:0 0 18px rgba(37,211,102,.55),0 0 36px rgba(37,211,102,.35),0 8px 24px rgba(37,211,102,.4)}50%{box-shadow:0 0 32px rgba(37,211,102,.95),0 0 64px rgba(37,211,102,.6),0 10px 30px rgba(37,211,102,.55)}}*::-webkit-scrollbar{width:6px}*::-webkit-scrollbar-thumb{background:#D6C4FF;border-radius:3px}`}</style>
    <Nav/>
    {pg==="home"&&Home()}
    {pg==="collections"&&Store()}
    {pg==="products"&&Products()}
    {pg==="collection"&&Collection()}
    {BookM()}{CkM()}{PM()}{AuthM()}{WA()}
    {personalizeBook&&<PersonalizeModal book={personalizeBook} onClose={()=>setPersonalizeBook(null)}/>}
  </div>;
}
