import data from "../../../data/mockData";

export default function HistoryTable(){

  return(

    <div className="card">

      <h3>Scan History</h3>

      <table>

        <thead>
          <tr>
            <th>ID</th>
            <th>Plate</th>
            <th>Time</th>
          </tr>
        </thead>

        <tbody>

        {data.map((item)=>(
          <tr key={item.id}>
            <td>{item.id}</td>
            <td>{item.plate}</td>
            <td>{item.time}</td>
          </tr>
        ))}

        </tbody>

      </table>

    </div>

  )

}