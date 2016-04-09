{
//=========Macro generated from canvas: c1/c1
//=========  (Mon Feb 29 12:14:26 2016) by ROOT version5.34/18
   TCanvas *c1 = new TCanvas("c1", "c1",1,1,700,476);
   c1->SetHighLightColor(2);
   c1->Range(475,0.4495528,725,1.084564);
   c1->SetFillColor(0);
   c1->SetBorderMode(0);
   c1->SetBorderSize(2);
   c1->SetFrameBorderMode(0);
   c1->SetFrameBorderMode(0);

   TF1 *expoRatio = new TF1("expoRatio","[0]*exp([1]*x)",500,700);
   expoRatio->SetFillColor(19);
   expoRatio->SetFillStyle(0);
   expoRatio->SetLineColor(2);
   expoRatio->SetLineWidth(2);
   expoRatio->GetXaxis()->SetLabelFont(42);
   expoRatio->GetXaxis()->SetLabelSize(0.035);
   expoRatio->GetXaxis()->SetTitleSize(0.035);
   expoRatio->GetXaxis()->SetTitleFont(42);
   expoRatio->GetYaxis()->SetLabelFont(42);
   expoRatio->GetYaxis()->SetLabelSize(0.035);
   expoRatio->GetYaxis()->SetTitleSize(0.035);
   expoRatio->GetYaxis()->SetTitleFont(42);
   expoRatio->SetParameter(0,0.1115778);
   expoRatio->SetParError(0,0);
   expoRatio->SetParLimits(0,0,0);
   expoRatio->SetParameter(1,0.003132904);
   expoRatio->SetParError(1,0);
   expoRatio->SetParLimits(1,0,0);
   expoRatio->Draw("");

   TPaveText *pt = new TPaveText(0.3843966,0.9339831,0.6156034,0.995,"blNDC");
   pt->SetName("title");
   pt->SetBorderSize(0);
   pt->SetFillColor(0);
   pt->SetFillStyle(0);
   pt->SetTextFont(42);
   TText *text = pt->AddText("[0]*exp([1]*x)");
   pt->Draw();
   c1->Modified();
   c1->cd();
   c1->SetSelected(c1);
}
