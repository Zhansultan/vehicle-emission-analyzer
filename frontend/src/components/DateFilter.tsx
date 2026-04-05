import { useState } from 'react';
import type { DateFilterProps } from '../types';

export function DateFilter({ onFilter }: DateFilterProps) {
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');

  const handleApply = () => {
    onFilter(dateFrom || undefined, dateTo || undefined);
  };

  const handleReset = () => {
    setDateFrom('');
    setDateTo('');
    onFilter(undefined, undefined);
  };

  return (
    <div className="date-filter">
      <h3>Filter by Date</h3>
      <div className="filter-inputs">
        <div className="input-group">
          <label htmlFor="date-from">From:</label>
          <input
            type="date"
            id="date-from"
            value={dateFrom}
            onChange={(e) => setDateFrom(e.target.value)}
          />
        </div>
        <div className="input-group">
          <label htmlFor="date-to">To:</label>
          <input
            type="date"
            id="date-to"
            value={dateTo}
            onChange={(e) => setDateTo(e.target.value)}
          />
        </div>
      </div>
      <div className="filter-buttons">
        <button type="button" onClick={handleApply} className="btn-primary">
          Apply
        </button>
        <button type="button" onClick={handleReset} className="btn-secondary">
          Reset
        </button>
      </div>
    </div>
  );
}
