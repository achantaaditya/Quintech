import Link from "next/link";
const routes = [["Overview","/dashboard"],["Resume","/dashboard/resume"],["Skills","/dashboard/skills"],["Roadmap","/dashboard/roadmap"],["Jobs","/dashboard/jobs"],["Interview","/dashboard/interview"],["Assistant","/dashboard/assistant"],["Profile","/dashboard/profile"]];
export function AppShell({children}:{children:React.ReactNode}){return <div className="app"><aside className="sidebar"><div className="brand">Career<span>OS</span></div>{routes.map(([name,href])=><Link key={href} href={href}>{name}</Link>)}</aside><main className="main">{children}</main></div>}
