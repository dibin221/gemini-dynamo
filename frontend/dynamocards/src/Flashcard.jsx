import React from 'react';
import { utils, writeFile } from 'xlsx';
import jsPDF from 'jspdf';

// Define the exportToExcel function
export const exportToExcel = (data, filename) => {
  const wb = utils.book_new();
  const ws = utils.json_to_sheet(data);
  utils.book_append_sheet(wb, ws, 'Sheet1');
  writeFile(wb, filename);
};

export const exportToPDF = (data, filename) => {
  const doc = new jsPDF();
  let yOffset = 10;
  const pageHeight = doc.internal.pageSize.height; // Get the height of the page
  const fontSize = 12; // Define the font size
  const gapBetweenConcepts = 2; // Define the reduced gap between concepts
  const gapBetweenTermAndDefinition = 1; // Define the reduced gap between term and definition

  data.forEach((concept, index) => {
    doc.setFontSize(fontSize); // Set the font size
    doc.setFont('helvetica', 'bold'); // Set font to bold
    const textLines = doc.splitTextToSize(concept.term, 180); // Split term into multiple lines
    const textHeight = textLines.length * 8;

    // Check if the content exceeds the page height
    if (yOffset + textHeight  + gapBetweenTermAndDefinition > pageHeight - gapBetweenConcepts) {
      doc.addPage(); // Add a new page
      yOffset = 5; // Reset yOffset for the new page
    }

    // Print term
    doc.text(textLines, 10, yOffset);
    doc.setFont('helvetica', 'normal'); // Reset font to normal
    yOffset += textHeight + gapBetweenTermAndDefinition; // Adjust yOffset

    const definitionLines = doc.splitTextToSize(concept.definition, 180); // Split definition into multiple lines
    doc.text(definitionLines, 15, yOffset);
    yOffset += (definitionLines.length * 8); // Adjust yOffset
    yOffset += gapBetweenConcepts; // Add some spacing between concepts
  });
  doc.save(filename);
};

const Flashcard = ({ term ,definition, onDiscard }) => {
  return (
    <div className="flashcard">
        <h3>{term}</h3>
        <p>{definition}</p>
        <button onClick={onDiscard} style={{marginTop: '10px'}}>Discard</button>
    </div>
  );
}

export default Flashcard;
