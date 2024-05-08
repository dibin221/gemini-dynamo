import React, { useState } from 'react';
import axios from 'axios';
import Flashcard, { exportToExcel ,exportToPDF} from './Flashcard';
import './Flashcard.css';

function App(){
  const [youtubeLink, setYoutubeLink] = useState("");
  const [keyConcepts,setKeyConcepts]=useState([]);
  const [errorMessage,setErrorMessage]=useState("");
  const [loading, setLoading] = useState(false);
  const [exportType, setExportType] = useState(null);
  const [exporting, setExporting] = useState(false);

  const handleLinkChange = (event)=> {
     setYoutubeLink(event.target.value);
  };

  const handleExport = () => {
    if (!exportType || !keyConcepts?.length) return;
    setExporting(true);
    switch (exportType) {
      case 'pdf': exportToPDF(keyConcepts, 'keyConcepts.pdf'); break;
      case 'excel': exportToExcel(keyConcepts, 'keyConcepts.xlsx'); break;
      default: break;
    }
    setExporting(false);
  };

  const sendLink = async () => {
    try {
      setLoading(true);
      // setKeyConcepts([]);
      const response = await axios.post("http://localhost:8000/analyze_video",{youtube_link:youtubeLink})
      const data =response.data
      setLoading(false);
      setErrorMessage("");
      if(data.key_concepts && Array.isArray(data.key_concepts)){
        setKeyConcepts(data.key_concepts);
      }
      else{
        console.log("Data does not contain key concepts..");
        setErrorMessage("Data does not contain key concepts..");
        setKeyConcepts([]);
        setLoading(false);
      }
    }catch(error){
      console.error(error);
      setErrorMessage("Error occurred. Please try again..!!!")
      setKeyConcepts([]);
      setLoading(false);
    }

  };

  const discardFlashcard = (index) => {
    setKeyConcepts(currentConcepts => currentConcepts.filter((_,i) => i !== index));
  };

  return(
    <div className="App" >
      <h1>Youtube Link to Flashcards Generator</h1>
      <span style={{ display: 'flex', alignItems: 'center' }}>
      <input
      type='text'
      placeholder='Paste Youtube Link Here'
      value={youtubeLink}
      onChange={handleLinkChange}
      />
      <button onClick={sendLink} disabled={loading}>Generate FlashCards</button>
      <div style={{ marginRight: '25px',marginLeft: '50px' }}>
        <input type="radio" id="pdf" name="exportType" value="pdf" checked={exportType === 'pdf'} onChange={() => setExportType('pdf')} disabled={exporting} />
        <label htmlFor="pdf">PDF</label>
        <br />
        <input type="radio" id="excel" name="exportType" value="excel" checked={exportType === 'excel'} onChange={() => setExportType('excel')} disabled={exporting} />
        <label htmlFor="excel">Excel</label>
      </div>
      <button onClick={handleExport} disabled={exporting}>Export</button>
      {exporting && <div>Exporting...</div>}
    </span>

      {/* Conditional rendering of the loading overlay */}
      {loading && (
        <div className="overlay">
          <div className="spinner"></div>
        </div>
      )}
{/*       {keyConcepts && (
        <div>
          <h1>Response Data</h1>
          <p>{JSON.stringify(keyConcepts,null,2)}</p>
        </div>
      )} */}
      <div>
      {errorMessage && <p>{errorMessage}</p>}
      </div>
      <div className="flashcardsContainer">
            {
              Array.isArray(keyConcepts) && keyConcepts.map((concept,index)=>(
                <Flashcard
                key={index}
                term={concept.term}
                definition={concept.definition}
                onDiscard={()=> discardFlashcard(index)}
                />
              ))
            }
        </div>
    </div>
  )
}
export default App;
