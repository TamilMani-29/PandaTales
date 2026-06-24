import PandoraApp from './pandora-pages-v3.jsx';
import AdminPage from './admin-page.jsx';

export default function App() {
  if (window.location.pathname.startsWith('/admin')) {
    return <AdminPage />;
  }

  return <PandoraApp />;
}
