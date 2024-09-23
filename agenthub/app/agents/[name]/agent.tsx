import React from 'react';
import { Card, CardBody, Chip, Tooltip, Snippet } from "@nextui-org/react";
import ReactMarkdown from 'react-markdown';
import { Clock, User, FileText, Info, Package } from 'lucide-react';

interface AgentFile {
  name: string;
  path: string;
}

export interface Agent {
  id: string;
  author: string;
  name: string;
  version: string;
  license: string;
  createdAt: string;
  updatedAt: string;
  description: string;
  files: AgentFile[];
}

export default function AgentDetailsPage({ agent }: { agent: Agent }) {
  return (
    <div className="w-full max-w-full m-0 p-8 bg-gray-50">
      <div className="mb-8 bg-gradient-to-r from-blue-500 to-purple-500 text-white p-6 rounded-lg shadow-md">
        <h1 className="text-4xl font-bold flex items-center gap-3 mb-2">
          <Package size={36} />
          {agent.name}
          <Chip size="sm" className="bg-white text-blue-600">{agent.version}</Chip>
        </h1>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-8">
          <Card className="shadow-md">
            <CardBody className="p-6">
              <h2 className="text-2xl font-semibold mb-4 text-gray-800">Agent Details</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="flex items-center">
                  <User className="mr-3 text-blue-500" size={24} />
                  <div>
                    <p className="text-sm text-gray-500">Author</p>
                    <p className="font-semibold">{agent.author}</p>
                  </div>
                </div>
                <div className="flex items-center">
                  <Clock className="mr-3 text-green-500" size={24} />
                  <div>
                    <p className="text-sm text-gray-500">Created</p>
                    <p className="font-semibold">{new Date(agent.createdAt).toLocaleDateString()}</p>
                  </div>
                </div>
                <div className="flex items-center">
                  <FileText className="mr-3 text-purple-500" size={24} />
                  <div>
                    <p className="text-sm text-gray-500">License</p>
                    <p className="font-semibold">{agent.license || "Unknown"}</p>
                  </div>
                </div>
                <div className="flex items-center">
                  <Clock className="mr-3 text-orange-500" size={24} />
                  <div>
                    <p className="text-sm text-gray-500">Last Updated</p>
                    <p className="font-semibold">{new Date(agent.updatedAt).toLocaleDateString()}</p>
                  </div>
                </div>
              </div>
            </CardBody>
          </Card>

          <Card className="shadow-md">
            <CardBody className="p-6">
              <h2 className="text-2xl font-semibold mb-4 text-gray-800">Description</h2>
              <div className="prose max-w-none">
                {agent.description ? (
                  <ReactMarkdown>{agent.description}</ReactMarkdown>
                ) : (
                  <p className="text-gray-500 italic">No description provided</p>
                )}
              </div>
            </CardBody>
          </Card>

          <Card className="shadow-md">
            <CardBody className="p-6">
              <h2 className="text-2xl font-semibold mb-4 text-gray-800">Files</h2>
              {agent.files.length > 0 ? (
                <ul className="space-y-3">
                  {agent.files.map((file, index) => (
                    <li key={index} className="flex items-center bg-gray-100 p-3 rounded-md">
                      <FileText className="mr-3 text-blue-500" size={20} />
                      <span className="font-medium">{file.name}</span>
                      <span className="text-gray-500 ml-2">- {file.path}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-gray-500 italic">No files available</p>
              )}
            </CardBody>
          </Card>
        </div>

        <div className="space-y-8">
          <Card className="shadow-md">
            <CardBody className="p-6 flex flex-col gap-y-4">
              
              <h2 className="text-2xl font-semibold mb-4 text-gray-800">Use this agent</h2>
              <Snippet color="secondary" symbol="" variant="flat">
                <span className=''>from pyopenagi.manager.manager import AgentManager</span>
                <span className=''>manager.download_agent(&apos;example&apos;, &apos;academic_agent&apos;)</span>
              </Snippet>
            </CardBody>
          </Card>

          <Card className="shadow-md">
            <CardBody className="p-6">
              <h3 className="font-semibold text-xl mb-4 text-gray-800">Agent Information</h3>
              <ul className="space-y-3">
                <li className="flex items-center justify-between bg-gray-100 p-3 rounded-md">
                  <span className="text-gray-700">Downloads</span>
                  <Tooltip content="Number of downloads">
                    <span className="flex items-center cursor-help">
                      <Info size={18} className="mr-2 text-blue-500" />
                      N/A
                    </span>
                  </Tooltip>
                </li>
                <li className="flex items-center justify-between bg-gray-100 p-3 rounded-md">
                  <span className="text-gray-700">Likes</span>
                  <Tooltip content="Number of likes">
                    <span className="flex items-center cursor-help">
                      <Info size={18} className="mr-2 text-blue-500" />
                      N/A
                    </span>
                  </Tooltip>
                </li>
              </ul>
            </CardBody>
          </Card>
        </div>
      </div>
    </div>
  );
}