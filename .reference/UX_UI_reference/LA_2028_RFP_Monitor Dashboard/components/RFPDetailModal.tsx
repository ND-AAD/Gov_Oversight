import { RFP } from '../types/rfp';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from './ui/dialog';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Separator } from './ui/separator';
import { 
  ExternalLink, 
  Calendar, 
  Building, 
  DollarSign, 
  Globe, 
  Hash,
  Clock,
  Copy,
  Download,
  Share,
  EyeOff
} from 'lucide-react';
import { format } from '../utils/dateUtils';
import { toast } from 'sonner@2.0.3';

interface RFPDetailModalProps {
  rfp: RFP | null;
  isOpen: boolean;
  onClose: () => void;
  onIgnore: (id: string) => void;
}

export function RFPDetailModal({ rfp, isOpen, onClose, onIgnore }: RFPDetailModalProps) {
  if (!rfp) return null;

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount);
  };

  const getStatusBadgeVariant = (status: string) => {
    switch (status) {
      case 'closing_soon':
        return 'destructive';
      case 'active':
        return 'default';
      case 'closed':
        return 'secondary';
      default:
        return 'outline';
    }
  };

  const handleCopyLink = () => {
    navigator.clipboard.writeText(window.location.href);
    toast.success('Link copied to clipboard');
  };

  const handleDownloadData = () => {
    const dataStr = JSON.stringify(rfp, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `rfp-${rfp.id}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    toast.success('RFP data downloaded');
  };

  const handleShare = () => {
    if (navigator.share) {
      navigator.share({
        title: rfp.title,
        text: rfp.description,
        url: window.location.href
      });
    } else {
      handleCopyLink();
    }
  };

  const handleIgnore = () => {
    onIgnore(rfp.id);
    onClose();
    toast.success('RFP ignored');
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1">
              <DialogTitle className="pr-8 leading-tight">
                {rfp.title}
              </DialogTitle>
              <DialogDescription className="sr-only">
                Detailed view of RFP including description, metadata, and action buttons
              </DialogDescription>
              <div className="flex flex-wrap gap-2 mt-3">
                <Badge variant={getStatusBadgeVariant(rfp.status)}>
                  {rfp.status.replace('_', ' ')}
                </Badge>
                {rfp.event_association && (
                  <Badge variant="outline" className="bg-blue-50">
                    {rfp.event_association}
                  </Badge>
                )}
                {rfp.procurement_type && (
                  <Badge variant="outline" className="bg-purple-50">
                    {rfp.procurement_type}
                  </Badge>
                )}
              </div>
            </div>
          </div>
        </DialogHeader>

        <div className="space-y-6">
          {/* Description */}
          <div>
            <h3 className="mb-3">Description</h3>
            <p className="text-muted-foreground leading-relaxed">
              {rfp.description}
            </p>
          </div>

          <Separator />

          {/* Metadata Grid */}
          <div>
            <h3 className="mb-4">Details</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-3">
                <div className="flex items-center gap-3">
                  <Hash className="h-4 w-4 text-muted-foreground" />
                  <div>
                    <p className="text-sm text-muted-foreground">RFP ID</p>
                    <p className="font-mono">{rfp.id}</p>
                  </div>
                </div>

                {rfp.issuer && (
                  <div className="flex items-center gap-3">
                    <Building className="h-4 w-4 text-muted-foreground" />
                    <div>
                      <p className="text-sm text-muted-foreground">Issuing Agency</p>
                      <p>{rfp.issuer}</p>
                    </div>
                  </div>
                )}

                <div className="flex items-center gap-3">
                  <Globe className="h-4 w-4 text-muted-foreground" />
                  <div>
                    <p className="text-sm text-muted-foreground">Source Website</p>
                    <p>{rfp.source_site}</p>
                  </div>
                </div>

                {rfp.contract_value && (
                  <div className="flex items-center gap-3">
                    <DollarSign className="h-4 w-4 text-green-600" />
                    <div>
                      <p className="text-sm text-muted-foreground">Contract Value</p>
                      <p className="font-medium text-green-600">
                        {formatCurrency(rfp.contract_value)}
                      </p>
                    </div>
                  </div>
                )}
              </div>

              <div className="space-y-3">
                <div className="flex items-center gap-3">
                  <Calendar className="h-4 w-4 text-muted-foreground" />
                  <div>
                    <p className="text-sm text-muted-foreground">Posted Date</p>
                    <p>{format(new Date(rfp.posted_date), 'MMMM dd, yyyy')}</p>
                  </div>
                </div>

                {rfp.closing_date && (
                  <div className="flex items-center gap-3">
                    <Calendar className="h-4 w-4 text-destructive" />
                    <div>
                      <p className="text-sm text-muted-foreground">Closing Date</p>
                      <p className="text-destructive">
                        {format(new Date(rfp.closing_date), 'MMMM dd, yyyy')}
                      </p>
                    </div>
                  </div>
                )}

                <div className="flex items-center gap-3">
                  <Clock className="h-4 w-4 text-muted-foreground" />
                  <div>
                    <p className="text-sm text-muted-foreground">Last Updated</p>
                    <p>{format(new Date(rfp.detected_at), 'MMMM dd, yyyy h:mm a')}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Categories */}
          {rfp.categories && rfp.categories.length > 0 && (
            <>
              <Separator />
              <div>
                <h3 className="mb-3">Categories</h3>
                <div className="flex flex-wrap gap-2">
                  {rfp.categories.map(category => (
                    <Badge key={category} variant="outline">
                      {category}
                    </Badge>
                  ))}
                </div>
              </div>
            </>
          )}

          <Separator />

          {/* Action Buttons */}
          <div className="flex flex-wrap gap-3">
            <Button asChild>
              <a 
                href={rfp.url} 
                target="_blank" 
                rel="noopener noreferrer"
                className="flex items-center gap-2"
              >
                <ExternalLink className="h-4 w-4" />
                View Original RFP
              </a>
            </Button>

            <Button 
              variant="outline"
              onClick={handleDownloadData}
              className="flex items-center gap-2"
            >
              <Download className="h-4 w-4" />
              Download Data
            </Button>

            <Button 
              variant="outline"
              onClick={handleShare}
              className="flex items-center gap-2"
            >
              <Share className="h-4 w-4" />
              Share
            </Button>

            <Button 
              variant="outline"
              onClick={handleCopyLink}
              className="flex items-center gap-2"
            >
              <Copy className="h-4 w-4" />
              Copy Link
            </Button>

            <Button 
              variant="destructive"
              onClick={handleIgnore}
              className="flex items-center gap-2"
            >
              <EyeOff className="h-4 w-4" />
              Ignore This RFP
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}