import React, { useState, useEffect } from "react";
import axios from "axios";

// Reusable sub-components
import StoreSelector from "./components/StoreSelector";
import WeeksInput from "./components/WeeksInput";
import ToggleButtons from "./components/ToggleButtons";

// Charts
import ForecastChart from "./components/ForecastChart";
import CompareChart from "./components/CompareChart";
import SeasonalityChart from "./components/SeasonalityChart";
import FeatureImportanceChart from "./components/FeatureImportanceChart";

// Summary Cards
import ForecastSummaryCard from "./components/ForecastSummaryCard";
import CompareSummaryCard from "./components/CompareSummaryCard";
import SeasonalitySummaryCard from "./components/SeasonalitySummaryCard";
import FeatureImportanceSummaryCard from "./components/FeatureImportanceSummaryCard";
import AiForecastSummaryCard from "./components/AiForecastSummaryCard";

// ✅ Auto-switch between localhost and production
const BASE_URL = "https://ml-forecast-api-bpa9g0hscaccc0e0.canadacentral-01.azurewebsites.net";


function App() {
  const [storeList, setStoreList] = useState([]);
  const [selectedStore, setSelectedStore] = useState("");
  const [weeks, setWeeks] = useState(4);

  const [forecastData, setForecastData] = useState([]);
  const [compareData, setCompareData] = useState([]);
  const [seasonalityData, setSeasonalityData] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [actionableData, setActionableData] = useState([]);
  const [conceptualData, setConceptualData] = useState([]);

  const [showForecast, setShowForecast] = useState(false);
  const [showCompare, setShowCompare] = useState(false);
  const [showSeasonality, setShowSeasonality] = useState(false);
  const [showMetrics, setShowMetrics] = useState(false);
  const [showFeatureImportance, setShowFeatureImportance] = useState(false);

  const [error, setError] = useState("");
  const [aiForecastSummary, setAiForecastSummary] = useState("");
  const [aiFeatureImportanceSummary, setAiFeatureImportanceSummary] = useState("");

  useEffect(() => {
    axios
      .get(`${BASE_URL}/stores`)
      .then((res) => setStoreList(res.data.stores))
      .catch(() => setError("Could not load store IDs"));
  }, []);

  const handleForecast = async () => {
    if (!selectedStore) return setError("Select a store first!");

    try {
      const res = await axios.post(`${BASE_URL}/predict`, {
        store: selectedStore,
        weeks: weeks,
      });

      if (res.data.prediction) {
        const chartData = res.data.prediction.map((val, idx) => ({
          week: idx + 1,
          predicted: parseFloat(val.predicted.toFixed(2)),
          upper: parseFloat(val.upper.toFixed(2)),
          lower: parseFloat(val.lower.toFixed(2)),
        }));
        setForecastData(chartData);
        setError("");

        const totalPredicted = chartData.reduce((acc, cur) => acc + cur.predicted, 0);
        const confidence_low = Math.min(...chartData.map((c) => c.lower));
        const confidence_high = Math.max(...chartData.map((c) => c.upper));

        const aiPayload = {
          store: selectedStore,
          forecastSummary: {
            totalPredicted: Math.round(totalPredicted),
            weeks: chartData.length,
            confidence_low: Math.round(confidence_low),
            confidence_high: Math.round(confidence_high),
          },
        };

        const aiRes = await axios.post(`${BASE_URL}/ai_summary`, aiPayload);
        if (aiRes.data.summary) {
          setAiForecastSummary(aiRes.data.summary);
        }
      } else {
        setForecastData([]);
        setError(res.data.error || "Prediction failed.");
      }
    } catch (err) {
      setError("Error connecting to backend for forecast.");
    }
  };

  const handleAiFeatureImportance = async () => {
    try {
      const payload = {
        actionable: actionableData,
        conceptual: conceptualData,
      };
      const res = await axios.post(`${BASE_URL}/ai_feature_importance`, payload);
      if (res.data.summary) {
        setAiFeatureImportanceSummary(res.data.summary);
        setError("");
      } else {
        setError("No summary returned from AI feature importance endpoint.");
      }
    } catch (err) {
      setError("Error fetching AI feature importance summary.");
    }
  };

  const handleCompare = async () => {
    if (!selectedStore) return setError("Select a store first!");
    try {
      const res = await axios.post(`${BASE_URL}/compare`, {
        store: selectedStore,
        num_points: 6,
      });
      if (res.data.data) {
        const compareVals = res.data.data.map((d) => ({
          monthLabel: `${d.year}-${String(d.month).padStart(2, "0")}`,
          actual: d.actual,
          predicted: d.predicted,
        }));
        setCompareData(compareVals);
        setError("");
      } else {
        setCompareData([]);
        setError("Compare request failed.");
      }
    } catch (err) {
      setError("Error connecting to backend for compare.");
    }
  };

  const handleSeasonality = async () => {
    try {
      const res = await axios.get(`${BASE_URL}/analysis/seasonality`);
      if (res.data.seasonality) {
        setSeasonalityData(res.data.seasonality);
        setError("");
      } else {
        setSeasonalityData([]);
        setError("Seasonality request failed.");
      }
    } catch (err) {
      setError("Error connecting to backend for seasonality.");
    }
  };

  const handleMetrics = async () => {
    try {
      const res = await axios.get(`${BASE_URL}/metrics`);
      setMetrics(res.data);
      setError("");
    } catch (err) {
      setError("Error fetching model metrics.");
    }
  };

  const handleFeatureImportance = async () => {
    try {
      const res = await axios.get(`${BASE_URL}/feature_importance`);
      if (res.data.actionable && res.data.conceptual) {
        setActionableData(res.data.actionable);
        setConceptualData(res.data.conceptual);
        setError("");
      } else {
        setError("No feature importances returned.");
      }
    } catch (err) {
      setError("Error fetching feature importances.");
    }
  };

  return (
    <div style={{ margin: "30px", fontFamily: "Arial" }}>
      <h1>Liquor Sales Forecast</h1>
      {error && <p style={{ color: "red" }}>{error}</p>}

      <div style={{ display: "flex", gap: "20px", marginBottom: "20px", alignItems: "center" }}>
        <StoreSelector
          storeList={storeList}
          selectedStore={selectedStore}
          setSelectedStore={setSelectedStore}
        />
        <WeeksInput weeks={weeks} setWeeks={setWeeks} />
      </div>

      <ToggleButtons
        showForecast={showForecast}
        setShowForecast={setShowForecast}
        handleForecast={handleForecast}
        showCompare={showCompare}
        setShowCompare={setShowCompare}
        handleCompare={handleCompare}
        showSeasonality={showSeasonality}
        setShowSeasonality={setShowSeasonality}
        handleSeasonality={handleSeasonality}
        showMetrics={showMetrics}
        setShowMetrics={setShowMetrics}
        handleMetrics={handleMetrics}
        showFeatureImportance={showFeatureImportance}
        setShowFeatureImportance={setShowFeatureImportance}
        handleFeatureImportance={handleFeatureImportance}
      />

      <hr />

      {showForecast && forecastData.length > 0 && (
        <div style={{ marginTop: "20px" }}>
          <h2>Forecast (Next {weeks} weeks)</h2>
          <ForecastSummaryCard selectedStore={selectedStore} forecastData={forecastData} />
          <AiForecastSummaryCard aiText={aiForecastSummary} />
          <ForecastChart data={forecastData} />
        </div>
      )}

      {showCompare && compareData.length > 0 && (
        <div style={{ marginTop: "20px" }}>
          <h2>Historic Compare (Last 6 weeks)</h2>
          <CompareSummaryCard compareData={compareData} />
          <CompareChart data={compareData} />
        </div>
      )}

      {showSeasonality && seasonalityData.length > 0 && (
        <div style={{ marginTop: "20px" }}>
          <h2>Seasonality Analysis</h2>
          <SeasonalitySummaryCard seasonalityData={seasonalityData} />
          <SeasonalityChart data={seasonalityData} />
        </div>
      )}

      {showFeatureImportance && (actionableData.length > 0 || conceptualData.length > 0) && (
        <div style={{ marginTop: "20px" }}>
          <h2>Model Feature Importances</h2>
          <button onClick={handleAiFeatureImportance} style={{ marginBottom: "10px" }}>
            {aiFeatureImportanceSummary ? "Refresh AI Summary" : "Generate AI Summary"}
          </button>
          {aiFeatureImportanceSummary && (
            <div style={{
              border: "1px solid #ccc",
              backgroundColor: "#f1f1f1",
              padding: "10px",
              marginBottom: "10px",
              borderRadius: "4px"
            }}>
              <strong>AI-Generated Feature Importance Summary</strong>
              <p>{aiFeatureImportanceSummary}</p>
            </div>
          )}
          <FeatureImportanceSummaryCard
            actionableData={actionableData}
            conceptualData={conceptualData}
          />
          <div style={{ display: "flex", gap: "40px" }}>
            {actionableData.length > 0 && (
              <div style={{ flex: 1 }}>
                <h3>Actionable Factors</h3>
                <FeatureImportanceChart data={actionableData} />
              </div>
            )}
            {conceptualData.length > 0 && (
              <div style={{ flex: 1 }}>
                <h3>Conceptual Factors</h3>
                <FeatureImportanceChart data={conceptualData} />
              </div>
            )}
          </div>
        </div>
      )}

      {showMetrics && metrics && (
        <div style={{ marginTop: "20px" }}>
          <h2>Model Performance Metrics</h2>
          <p>MAE: {metrics.MAE}</p>
          <p>RMSE: {metrics.RMSE}</p>
        </div>
      )}
    </div>
  );
}

export default App;
