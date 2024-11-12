'use client';
import { useEffect, useState } from 'react';

export default function PDFDownloadPage() {
    const [params, setParams] = useState({
        storeid: '',
        year: new Date().getFullYear(),
        month: new Date().getMonth() + 1
    });

    const downloadPdf = async () => {
        if (!params.storeid) {
            alert('가게 ID를 입력해주세요.');
            return;
        }

        const token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJwYXlsb2FkIjoicDdSaTF3YTE5YUcrZEtSRGpwZlg1Zz09IiwiaWF0IjoxNzMxMDM2NzIzLCJleHAiOjE3Mzk2NzY3MjN9._ieJm9kPR0FZEy42zQMG9UE-X9jjmJnGclOckQbkQMA";
        
        try {
            console.log('요청 시작');
            const requestUrl = new URL('http://localhost:8888/finance/transactionpdf');
            requestUrl.searchParams.append('storeid', params.storeid);
            requestUrl.searchParams.append('year', params.year);
            requestUrl.searchParams.append('month', params.month);

            const response = await fetch(requestUrl.toString(), {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Accept': 'application/pdf',
                    'Content-Type': 'application/json'
                }
            });

            console.log('응답 상태:', response.status);
            console.log('응답 헤더:', [...response.headers.entries()]);

            if (!response.ok) {
                console.log('응답이 올바르지 않음:', response.status, response.statusText);
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const blob = await response.blob();
            console.log('Blob 정보:', {
                size: blob.size,
                type: blob.type
            });

            if (blob.size === 0) {
                throw new Error('PDF 내용이 비어있습니다');
            }

            // Blob URL 생성
            const pdfUrl = window.URL.createObjectURL(blob);
            console.log('생성된 URL:', pdfUrl);

            // 다운로드
            const a = document.createElement('a');
            a.href = pdfUrl;
            a.download = `손익계산서_${params.year}_${params.month}.pdf`;  // 파일명에 년월 추가
            document.body.appendChild(a);
            console.log('다운로드 링크 생성됨');
            a.click();
            document.body.removeChild(a);

            // 미리보기
            const viewer = document.getElementById('pdfViewer');
            if (viewer) {
                viewer.src = pdfUrl;
                console.log('미리보기 설정됨');
            }

            // Cleanup - URL 정리
            setTimeout(() => {
                window.URL.revokeObjectURL(pdfUrl);
                console.log('URL 정리됨');
            }, 5000);

        } catch (error) {
            console.error('상세 에러 정보:', error);
            alert('PDF 다운로드 실패: ' + error.message);
        }
    };

    return (
        <div>
            <h1>PDF 다운로드 테스트</h1>
            
            <div style={{ marginBottom: '20px' }}>
                <div>
                    <label>가게 ID: </label>
                    <input 
                        type="number" 
                        value={params.storeid}
                        onChange={(e) => setParams(prev => ({...prev, storeid: e.target.value}))}
                    />
                </div>
                <div>
                    <label>년도: </label>
                    <input 
                        type="number" 
                        value={params.year}
                        onChange={(e) => setParams(prev => ({...prev, year: e.target.value}))}
                    />
                </div>
                <div>
                    <label>월: </label>
                    <input 
                        type="number" 
                        value={params.month}
                        min="1"
                        max="12"
                        onChange={(e) => setParams(prev => ({...prev, month: e.target.value}))}
                    />
                </div>
            </div>
            
            <button onClick={downloadPdf}>PDF 다운로드</button>
            
            <div style={{ marginTop: '20px' }}>
                <h3>PDF 미리보기</h3>
                <iframe 
                    id="pdfViewer" 
                    style={{ width: '100%', height: '500px' }}
                />
            </div>
        </div>
    );
}
