import Navbar from "../assets/components/layout/Navbar"
import UploadImage from "../assets/components/scanner/UploadImage"
import ResultCard from "../assets/components/scanner/ResultCard"
import HistoryTable from "../assets/components/history/HistoryTable"

export default function Dashboard() {
  return (
    <div>
      <Navbar />

      <div className="container">
        <div className="grid">
          <UploadImage />
          <ResultCard />
        </div>

        <HistoryTable />
      </div>
    </div>
  )
}