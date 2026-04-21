import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { formatPrice, formatPercent, priceChange } from "@/lib/utils";
import type { PriceData } from "@/types";

interface PriceChartProps {
  priceData: PriceData;
  ticker: string;
}

export function PriceChart({ priceData, ticker }: PriceChartProps) {
  if (!priceData.price_available) {
    return (
      <div className="card p-6">
        <h3 className="font-display font-semibold text-stone-900 mb-1">
          Price movement
        </h3>
        <p className="text-sm text-stone-400 mt-4 text-center py-8">
          Price data unavailable for {ticker}
        </p>
      </div>
    );
  }

  const data = [
    {
      label: "Call date",
      price: priceData.price_on_call_date,
    },
    {
      label: "Next day",
      price: priceData.price_day_after,
    },
    {
      label: "One week",
      price: priceData.price_week_after,
    },
  ].filter((d) => d.price !== null);

  const changeD1 = priceChange(priceData.price_on_call_date, priceData.price_day_after);
  const changeW1 = priceChange(priceData.price_on_call_date, priceData.price_week_after);
  const isPositive = (changeW1 ?? changeD1 ?? 0) >= 0;

  return (
    <div className="card p-6">
      <div className="flex items-start justify-between mb-6">
        <div>
          <h3 className="font-display font-semibold text-stone-900">
            Price movement
          </h3>
          {priceData.call_date && (
            <p className="text-xs text-stone-400 mt-0.5">
              Call date: {priceData.call_date}
            </p>
          )}
        </div>

        <div className="flex items-center gap-4 text-right">
          <div>
            <p className="text-xs text-stone-400 mb-0.5">Next day</p>
            <p className={`text-sm font-medium ${changeD1 !== null && changeD1 >= 0 ? "text-green-600" : "text-red-600"}`}>
              {formatPercent(changeD1)}
            </p>
          </div>
          <div>
            <p className="text-xs text-stone-400 mb-0.5">One week</p>
            <p className={`text-sm font-medium ${changeW1 !== null && changeW1 >= 0 ? "text-green-600" : "text-red-600"}`}>
              {formatPercent(changeW1)}
            </p>
          </div>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={160}>
        <AreaChart data={data} margin={{ top: 4, right: 4, left: 4, bottom: 0 }}>
          <defs>
            <linearGradient id="priceGradient" x1="0" y1="0" x2="0" y2="1">
              <stop
                offset="5%"
                stopColor={isPositive ? "#16A34A" : "#DC2626"}
                stopOpacity={0.15}
              />
              <stop
                offset="95%"
                stopColor={isPositive ? "#16A34A" : "#DC2626"}
                stopOpacity={0}
              />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#F0EDE9" vertical={false} />
          <XAxis
            dataKey="label"
            tick={{ fontSize: 11, fill: "#9A9088" }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            tick={{ fontSize: 11, fill: "#9A9088" }}
            axisLine={false}
            tickLine={false}
            tickFormatter={(v) => `$${v.toFixed(0)}`}
            width={45}
          />
          <Tooltip
            contentStyle={{
              background: "#fff",
              border: "1px solid #E8E5E1",
              borderRadius: "10px",
              fontSize: "12px",
              boxShadow: "0 4px 12px rgba(40,36,31,0.08)",
            }}
            formatter={(value: number) => [formatPrice(value), "Price"]}
          />
          <Area
            type="monotone"
            dataKey="price"
            stroke={isPositive ? "#16A34A" : "#DC2626"}
            strokeWidth={2}
            fill="url(#priceGradient)"
            dot={{ fill: isPositive ? "#16A34A" : "#DC2626", r: 4, strokeWidth: 0 }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
