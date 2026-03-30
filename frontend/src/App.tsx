import { useEffect, useState } from 'react';
import { TopNavigation, Brand, Navigation } from './components/layout/Header';
import { HomePage } from './pages/HomePage';
import { PickerPage } from './pages/PickerPage';
import { DetailPage } from './pages/DetailPage';
import { ComparePage } from './pages/ComparePage';
import { WatchlistPage } from './pages/WatchlistPage';
import {
  addWatchlist,
  fetchFunds,
  fetchWatchlist,
  fetchFundDetail,
  refreshMarket,
  removeWatchlist,
} from './api';
import type { FundScore, RiskProfile, FundDetail } from './types';

type Page = '首页' | '选基' | '详情' | '对比' | '观察池';

export function App() {
  const [page, setPage] = useState<Page>('首页');
  const [risk, setRisk] = useState<RiskProfile>('均衡');
  const [funds, setFunds] = useState<FundScore[]>([]);
  const [loading, setLoading] = useState(false);
  const [refreshingMarket, setRefreshingMarket] = useState(false);
  const [watchlist, setWatchlist] = useState<FundScore[]>([]);
  const [detailCode, setDetailCode] = useState<string | null>(null);
  const [detailData, setDetailData] = useState<FundDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [error, setError] = useState('');

  // Load funds on mount and when risk profile changes
  useEffect(() => {
    loadFunds();
  }, [risk]);

  // Load watchlist
  useEffect(() => {
    loadWatchlist();
  }, [risk]);

  // Load detail when detailCode changes
  useEffect(() => {
    if (detailCode && page === '详情') {
      loadDetail(detailCode);
    }
  }, [detailCode, page, risk]);

  async function loadFunds() {
    setLoading(true);
    setError('');
    try {
      const data = await fetchFunds({
        risk_profile: risk,
        page: 1,
        page_size: 50,
        sort_by: 'final_score',
        sort_order: 'desc',
      });
      setFunds(data.items);
    } catch (e: unknown) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }

  async function loadWatchlist() {
    try {
      const data = await fetchWatchlist(risk);
      setWatchlist(data);
    } catch (e: unknown) {
      console.error('Failed to load watchlist:', e);
    }
  }

  async function loadDetail(code: string) {
    setDetailLoading(true);
    setError('');
    try {
      const data = await fetchFundDetail(code, risk);
      setDetailData(data);
    } catch (e: unknown) {
      setError((e as Error).message);
    } finally {
      setDetailLoading(false);
    }
  }

  async function handleRefreshMarket() {
    try {
      setRefreshingMarket(true);
      setError('');
      await refreshMarket();
      await loadFunds();
      await loadWatchlist();
      if (detailCode) {
        await loadDetail(detailCode);
      }
    } catch (e: unknown) {
      setError((e as Error).message);
    } finally {
      setRefreshingMarket(false);
    }
  }

  async function handleAddWatchlist(code: string) {
    try {
      await addWatchlist(code);
      await loadWatchlist();
    } catch (e: unknown) {
      setError((e as Error).message);
    }
  }

  async function handleRemoveWatchlist(code: string) {
    try {
      await removeWatchlist(code);
      await loadWatchlist();
    } catch (e: unknown) {
      setError((e as Error).message);
    }
  }

  function handleViewDetail(code: string) {
    setDetailCode(code);
    setPage('详情');
  }

  function handleBackFromDetail() {
    setDetailCode(null);
    setDetailData(null);
    setPage('首页');
  }

  const navItems = [
    { label: '首页', active: page === '首页', onClick: () => setPage('首页') },
    { label: '选基', active: page === '选基', onClick: () => setPage('选基') },
    { label: '对比', active: page === '对比', onClick: () => setPage('对比') },
    { label: '观察池', active: page === '观察池', onClick: () => setPage('观察池') },
  ];

  return (
    <div style={{ minHeight: '100vh', backgroundColor: 'var(--color-background)' }}>
      {/* Top Navigation */}
      <TopNavigation>
        <Brand />
        <Navigation items={navItems} />
      </TopNavigation>

      {/* Error Banner */}
      {error && (
        <div
          style={{
            padding: '14px 18px',
            margin: '0 32px 16px',
            borderRadius: '16px',
            backgroundColor: '#FFDAD6',
            color: '#93000A',
          }}
        >
          错误：{error}
        </div>
      )}

      {/* Main Content */}
      <main>
        {page === '首页' && (
          <HomePage
            riskProfile={risk}
            onRiskProfileChange={setRisk}
            funds={funds}
            loading={loading}
            onRefreshMarket={handleRefreshMarket}
            refreshingMarket={refreshingMarket}
            onViewDetail={handleViewDetail}
            onAddToWatchlist={handleAddWatchlist}
          />
        )}

        {page === '选基' && (
          <PickerPage
            funds={funds}
            loading={loading}
            onFilterChange={() => {}}
            onViewDetail={handleViewDetail}
            onAddToWatchlist={handleAddWatchlist}
          />
        )}

        {page === '对比' && <ComparePage funds={watchlist.slice(0, 5)} loading={loading} />}

        {page === '观察池' && (
          <WatchlistPage
            items={watchlist}
            loading={loading}
            onRemove={handleRemoveWatchlist}
            onViewDetail={handleViewDetail}
          />
        )}

        {page === '详情' && detailCode && (
          <DetailPage
            code={detailCode}
            data={detailData}
            loading={detailLoading}
            onBack={handleBackFromDetail}
          />
        )}
      </main>

      {/* Footer */}
      <footer
        style={{
          borderTop: '1px solid var(--color-border-strong)',
          marginTop: '48px',
          padding: '48px 0',
          textAlign: 'center',
        }}
      >
        <div className="container">
          <div className="flex justify-center gap-md" style={{ fontSize: '12px', color: 'var(--color-text-muted)' }}>
            <span>关于我们</span>
            <span>服务协议</span>
            <span>隐私政策</span>
            <span>风险揭示书</span>
          </div>
          <div className="mt-md" style={{ fontSize: '12px', color: 'var(--color-text-muted)' }}>
            仅供参考，不构成投资建议
          </div>
        </div>
      </footer>
    </div>
  );
}
