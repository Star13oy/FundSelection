import { useEffect, useRef, useState } from 'react';
import { TopNavigation, Brand, Navigation } from './components/layout/Header';
import { HomePage } from './pages/HomePage';
import { PickerPage } from './pages/PickerPage';
import { DetailPage } from './pages/DetailPage';
import { ComparePage } from './pages/ComparePage';
import { WatchlistPage } from './pages/WatchlistPage';
import {
  addWatchlist,
  fetchFunds,
  fetchRefreshMarketStatus,
  fetchSectorHeat,
  fetchWatchlist,
  fetchFundDetail,
  refreshMarket,
  removeWatchlist,
} from './api';
import type { FundScore, RiskProfile, FundDetail, SectorHeatItem } from './types';

type Page = '首页' | '选基' | '详情' | '对比' | '观察池';
type PickerFilters = {
  channel: string;
  category: string;
  min_years: string;
  max_fee: string;
  keyword: string;
};

export function App() {
  const riskProfiles: RiskProfile[] = ['保守', '均衡', '进取'];
  const [page, setPage] = useState<Page>('首页');
  const [risk, setRisk] = useState<RiskProfile>('均衡');
  const [funds, setFunds] = useState<FundScore[]>([]);
  const [loading, setLoading] = useState(false);
  const [refreshingMarket, setRefreshingMarket] = useState(false);
  const [watchlist, setWatchlist] = useState<FundScore[]>([]);
  const [fundsCache, setFundsCache] = useState<Partial<Record<RiskProfile, FundScore[]>>>({});
  const [watchlistCache, setWatchlistCache] = useState<Partial<Record<RiskProfile, FundScore[]>>>({});
  const [sectorHeat, setSectorHeat] = useState<SectorHeatItem[]>([]);
  const [pickerFunds, setPickerFunds] = useState<FundScore[]>([]);
  const [pickerLoading, setPickerLoading] = useState(false);
  const [pickerPage, setPickerPage] = useState(1);
  const [pickerPageSize] = useState(20);
  const [pickerTotal, setPickerTotal] = useState(0);
  const [pickerFilters, setPickerFilters] = useState<PickerFilters>({
    channel: '',
    category: '',
    min_years: '',
    max_fee: '',
    keyword: '',
  });
  const [detailCode, setDetailCode] = useState<string | null>(null);
  const [detailData, setDetailData] = useState<FundDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [error, setError] = useState('');
  const riskRef = useRef<RiskProfile>(risk);

  useEffect(() => {
    riskRef.current = risk;
  }, [risk]);

  // Load funds on mount and when risk profile changes
  useEffect(() => {
    if (fundsCache[risk]) {
      setFunds(fundsCache[risk] ?? []);
      return;
    }
    void loadFunds(risk, { apply: true });
  }, [risk]);

  // Load watchlist
  useEffect(() => {
    if (watchlistCache[risk]) {
      setWatchlist(watchlistCache[risk] ?? []);
      return;
    }
    void loadWatchlist(risk, { apply: true });
  }, [risk]);

  // Load detail when detailCode changes
  useEffect(() => {
    if (detailCode && page === '详情') {
      loadDetail(detailCode);
    }
  }, [detailCode, page, risk]);

  useEffect(() => {
    if (page === '选基') {
      void loadPickerFunds();
    }
  }, [page, risk, pickerPage, pickerFilters]);

  useEffect(() => {
    void loadSectorHeat();
  }, []);

  useEffect(() => {
    riskProfiles
      .filter((profile) => profile !== risk)
      .forEach((profile) => {
        if (!fundsCache[profile]) {
          void loadFunds(profile, { apply: false });
        }
        if (!watchlistCache[profile]) {
          void loadWatchlist(profile, { apply: false });
        }
      });
  }, [risk, fundsCache, watchlistCache]);

  async function loadFunds(targetRisk: RiskProfile = risk, options: { apply: boolean; force?: boolean } = { apply: true }) {
    if (!options.force && fundsCache[targetRisk]) {
      if (options.apply) {
        setFunds(fundsCache[targetRisk] ?? []);
      }
      return;
    }
    if (options.apply) {
      setLoading(true);
      setError('');
    }
    try {
      const data = await fetchFunds({
        risk_profile: targetRisk,
        page: 1,
        page_size: 20,
        sort_by: 'final_score',
        sort_order: 'desc',
      });
      setFundsCache((prev) => ({ ...prev, [targetRisk]: data.items }));
      if (options.apply && riskRef.current === targetRisk) {
        setFunds(data.items);
      }
    } catch (e: unknown) {
      if (options.apply) {
        setError((e as Error).message);
      }
    } finally {
      if (options.apply) {
        setLoading(false);
      }
    }
  }

  async function loadWatchlist(targetRisk: RiskProfile = risk, options: { apply: boolean; force?: boolean } = { apply: true }) {
    if (!options.force && watchlistCache[targetRisk]) {
      if (options.apply) {
        setWatchlist(watchlistCache[targetRisk] ?? []);
      }
      return;
    }
    try {
      const data = await fetchWatchlist(targetRisk);
      setWatchlistCache((prev) => ({ ...prev, [targetRisk]: data }));
      if (options.apply && riskRef.current === targetRisk) {
        setWatchlist(data);
      }
    } catch (e: unknown) {
      if (options.apply) {
        console.error('Failed to load watchlist:', e);
      }
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

  async function loadSectorHeat() {
    try {
      const data = await fetchSectorHeat();
      setSectorHeat(data);
    } catch (e: unknown) {
      console.error('Failed to load sector heat:', e);
    }
  }

  async function loadPickerFunds() {
    setPickerLoading(true);
    setError('');
    try {
      const data = await fetchFunds({
        risk_profile: risk,
        page: pickerPage,
        page_size: pickerPageSize,
        channel: pickerFilters.channel === '场内' || pickerFilters.channel === '场外'
          ? pickerFilters.channel
          : undefined,
        category: pickerFilters.category || undefined,
        min_years: pickerFilters.min_years ? Number(pickerFilters.min_years) : undefined,
        max_fee: pickerFilters.max_fee ? Number(pickerFilters.max_fee) : undefined,
        keyword: pickerFilters.keyword || undefined,
        sort_by: 'final_score',
        sort_order: 'desc',
      });
      setPickerFunds(data.items);
      setPickerTotal(data.total);
    } catch (e: unknown) {
      setError((e as Error).message);
    } finally {
      setPickerLoading(false);
    }
  }

  async function handleRefreshMarket() {
    try {
      setRefreshingMarket(true);
      setError('');
      const response = await refreshMarket();
      if (response.status === 'completed') {
        setFundsCache({});
        setWatchlistCache({});
        await Promise.all([
          loadFunds(riskRef.current, { apply: true, force: true }),
          loadWatchlist(riskRef.current, { apply: true, force: true }),
        ]);
        await loadSectorHeat();
        if (detailCode) await loadDetail(detailCode);
        setRefreshingMarket(false);
        return;
      }
      void pollRefreshCompletion();
    } catch (e: unknown) {
      setError((e as Error).message);
      setRefreshingMarket(false);
    }
  }

  async function pollRefreshCompletion() {
    try {
      for (let attempt = 0; attempt < 60; attempt += 1) {
        await new Promise((resolve) => setTimeout(resolve, 2000));
        const status = await fetchRefreshMarketStatus();
        if (status.status === 'completed') {
          setFundsCache({});
          setWatchlistCache({});
          await Promise.all([
            loadFunds(riskRef.current, { apply: true, force: true }),
            loadWatchlist(riskRef.current, { apply: true, force: true }),
          ]);
          await loadSectorHeat();
          if (detailCode) await loadDetail(detailCode);
          return;
        }
        if (status.status === 'failed') {
          throw new Error(status.error || '行情后台刷新失败');
        }
      }
      throw new Error('行情刷新超时，请稍后再试');
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

  function handlePickerFilterChange(nextFilters: PickerFilters) {
    setPickerPage(1);
    setPickerFilters(nextFilters);
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
            sectorHeat={sectorHeat}
          />
        )}

        {page === '选基' && (
          <PickerPage
            funds={pickerFunds}
            total={pickerTotal}
            page={pickerPage}
            pageSize={pickerPageSize}
            loading={pickerLoading}
            filters={pickerFilters}
            onFilterChange={handlePickerFilterChange}
            onPageChange={setPickerPage}
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
