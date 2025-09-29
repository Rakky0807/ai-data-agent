import React from 'react';
import DataTable from './DataTable';
import DynamicChart from './Chart';

const Message = ({ message }) => {
  const { sender, text, data, chart } = message;
  const isAi = sender === 'ai';

  return (
    <div className={`message ${isAi ? 'ai-message' : 'user-message'}`}>
      <div className="message-bubble">
        <p>{text}</p>
        {chart && <DynamicChart chartSpec={chart} />}
        {data && <DataTable data={data} />}
      </div>
    </div>
  );
};

export default Message;