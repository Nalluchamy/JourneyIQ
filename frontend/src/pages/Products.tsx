import React from 'react';
import { Package, HelpCircle } from 'lucide-react';

export const Products: React.FC = () => {
  return (
    <div className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8">
      <div className="text-center py-20 border border-dashed border-border rounded-3xl bg-card/20">
        <Package className="mx-auto h-12 w-12 text-muted-foreground animate-pulse mb-4" />
        <h1 className="text-3xl font-extrabold text-white sm:text-4xl">Products</h1>
        <p className="mx-auto mt-4 max-w-md text-muted-foreground">
          JourneyIQ product personalization configuration dashboard will be implemented in
          subsequent phases.
        </p>

        <div className="mt-8 inline-flex items-center space-x-2 rounded-full border border-border bg-muted/40 px-4 py-1.5 text-xs text-muted-foreground">
          <HelpCircle className="h-3.5 w-3.5" />
          <span>Placeholder Component (Phase 1)</span>
        </div>
      </div>
    </div>
  );
};
