import React, { useEffect, useState, useCallback, useMemo } from "react";
import { observer } from "mobx-react-lite";
import { Light as SyntaxHighlighter } from "react-syntax-highlighter";
import json from "react-syntax-highlighter/dist/esm/languages/hljs/json";
import py from "react-syntax-highlighter/dist/esm/languages/hljs/python";
import atomOneLight from "react-syntax-highlighter/dist/esm/styles/hljs/atom-one-light";
import atomOneDark from "react-syntax-highlighter/dist/esm/styles/hljs/atom-one-dark";
import type { IChart } from "@kanaries/graphic-walker/interfaces";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import commonStore from "@/store/common";
import { darkModeContext } from "@/store/context";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { tracker } from "@/utils/tracker";
import { exportService } from "../../services/export";

SyntaxHighlighter.registerLanguage("json", json);
SyntaxHighlighter.registerLanguage("python", py);

const CodeExport: React.FC = observer(() => {
    const [visSpec, setVisSpec] = useState<IChart[]>([]);
    const [tips, setTips] = useState<string>("");
    const darkMode = React.useContext(darkModeContext);

    const pyCode = useMemo(() => {
        return exportService.generatePythonCode(commonStore.sourceInvokeCode, visSpec, commonStore.version);
    }, [commonStore.sourceInvokeCode, visSpec, commonStore.version]);

    const jsonCode = useMemo(() => {
        return exportService.generateJsonCode(visSpec);
    }, [visSpec]);

    const closeModal = useCallback(() => {
        commonStore.closeModal("codeExport");
    }, []);

    const copyToCliboard = async (content: string) => {
        const success = await exportService.copyPythonCode(commonStore.sourceInvokeCode, visSpec, commonStore.version);
        if (success) {
            commonStore.closeModal("codeExport");
        } else {
            setTips("The Clipboard API has been blocked in this environment. Please copy manully.");
        }
    };

    useEffect(() => {
        if (commonStore.codeExportModalOpen && commonStore.storeRef?.current) {
            const res = commonStore.storeRef.current.exportCode();
            setVisSpec(res);
        }
    }, [commonStore.codeExportModalOpen]);

    return (
        <Dialog
            open={commonStore.codeExportModalOpen}
            modal={false}
            onOpenChange={(show) => {
                commonStore.setCodeExportModalOpen(show);
            }}
        >
            <DialogContent className="sm:max-w-[90%] lg:max-w-[900px]">
                <DialogHeader>
                    <DialogTitle>Code Export</DialogTitle>
                    <DialogDescription>
                        Export the code of all charts in PyGWalker.
                    </DialogDescription>
                </DialogHeader>
                <div className="text-sm max-h-64 overflow-auto p-1">
                    <Tabs defaultValue="python" className="w-full">
                        <TabsList>
                            <TabsTrigger value="python">Python</TabsTrigger>
                            <TabsTrigger value="json">JSON(Graphic Walker)</TabsTrigger>
                        </TabsList>
                        <TabsContent className="py-4" value="python">
                            <h3 className="text-sm font-medium mb-2">PyGWalker Code</h3>
                            <SyntaxHighlighter showLineNumbers language="python" style={darkMode === 'dark' ? atomOneDark : atomOneLight}>
                                {pyCode}
                            </SyntaxHighlighter>
                            <div className="text-xs max-h-56 mt-2">
                                <p>{tips}</p>
                            </div>
                            <div className="mt-4 flex justify-start gap-2">
                                <Button
                                    onClick={() => {
                                        copyToCliboard(pyCode);
                                    }}
                                >
                                    Copy to Clipboard
                                </Button>
                                <Button variant="outline" onClick={closeModal}>
                                    Cancel
                                </Button>
                            </div>
                        </TabsContent>
                        <TabsContent value="json">
                            <h3 className="text-sm font-medium mb-2">Graphic Walker Specification</h3>
                            <SyntaxHighlighter showLineNumbers language="json" style={darkMode === 'dark' ? atomOneDark : atomOneLight}>
                                {jsonCode}
                            </SyntaxHighlighter>
                            <div className="text-xs max-h-56 mt-2">
                                <p>{tips}</p>
                            </div>
                            <div className="mt-4 flex justify-start gap-2">
                                <Button
                                    onClick={async () => {
                                        const success = await exportService.copyJsonCode(visSpec);
                                        if (success) {
                                            commonStore.closeModal("codeExport");
                                        } else {
                                            setTips("The Clipboard API has been blocked in this environment. Please copy manully.");
                                        }
                                        tracker.track("click", {"entity": "copy_code_button"});
                                    }}
                                >
                                    Copy to Clipboard
                                </Button>
                                <Button variant="outline" onClick={closeModal}>Cancel</Button>
                            </div>
                        </TabsContent>
                    </Tabs>
                </div>
            </DialogContent>
        </Dialog>
    );
});

export default CodeExport;
