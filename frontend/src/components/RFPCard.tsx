import type { RFP } from '../types/rfp';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from './ui/card';
import { ExternalLink, Calendar, Building, DollarSign, Eye, EyeOff, Star } from 'lucide-react';

interface RFPCardProps {
  rfp: RFP;
  onViewDetails: (rfp: RFP) => void;
  onIgnore: (id: string) => void;
  onToggleStar?: (id: string) => void;
  isIgnored?: boolean;
  isStarred?: boolean;
}

export function RFPCard({ 
  rfp, 
  onViewDetails, 
  onIgnore, 
  onToggleStar,
  isIgnored = false,
  isStarred = false 
}: RFPCardProps) {
  const formatCurrency = (amount: number) => {
    if (!amount) return null;
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount);
  };

  const format = (date: Date) => {
    // Simple date formatting - in a real app you'd use date-fns or similar
    const options: Intl.DateTimeFormatOptions = {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    };
    return date.toLocaleDateString('en-US', options);
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

  const getEventAssociationColor = (association: string) => {
    switch (association) {
      case 'Olympics 2028':
        return 'bg-blue-100 text-blue-800 hover:bg-blue-200';
      case 'World Cup 2026':
        return 'bg-green-100 text-green-800 hover:bg-green-200';
      default:
        return 'bg-gray-100 text-gray-800 hover:bg-gray-200';
    }
  };

  const getProcurementTypeColor = (type: string) => {
    switch (type) {
      case 'Technology':
        return 'bg-purple-100 text-purple-800 hover:bg-purple-200';
      case 'Construction':
        return 'bg-orange-100 text-orange-800 hover:bg-orange-200';
      case 'Services':
        return 'bg-cyan-100 text-cyan-800 hover:bg-cyan-200';
      case 'Equipment':
        return 'bg-yellow-100 text-yellow-800 hover:bg-yellow-200';
      default:
        return 'bg-gray-100 text-gray-800 hover:bg-gray-200';
    }
  };

  // Access flattened properties from enhanced RFP
  const issuer = (rfp as any).issuer || '';
  const eventAssociation = (rfp as any).event_association || '';
  const procurementType = (rfp as any).procurement_type || '';
  const contractValue = (rfp as any).contract_value || '';
  const status = (rfp as any).status || 'active';

  return (
    <Card className={`h-full flex flex-col group hover:shadow-lg transition-all duration-200 ${isIgnored ? 'opacity-60 grayscale' : ''} relative`}>
      {/* Star button in top right corner */}
      {onToggleStar && (
        <Button
          variant="ghost"
          size="sm"
          onClick={() => onToggleStar(rfp.id)}
          className={`absolute top-2 right-2 z-10 p-1 h-auto w-auto ${
            isStarred 
              ? 'text-yellow-500 hover:text-yellow-600' 
              : 'text-muted-foreground hover:text-foreground'
          }`}
        >
          <Star className={`h-4 w-4 ${isStarred ? 'fill-current' : ''}`} />
        </Button>
      )}

      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-2 pr-8">
          <CardTitle 
            className="cursor-pointer hover:text-primary transition-colors line-clamp-2"
            onClick={() => onViewDetails(rfp)}
          >
            {rfp.title}
          </CardTitle>
          <Badge variant={getStatusBadgeVariant(status)}>
            {status.replace('_', ' ')}
          </Badge>
        </div>
        
        <div className="flex flex-wrap gap-2 mt-2">
          {eventAssociation && (
            <Badge 
              variant="outline" 
              className={getEventAssociationColor(eventAssociation)}
            >
              {eventAssociation}
            </Badge>
          )}
          {procurementType && (
            <Badge 
              variant="outline" 
              className={getProcurementTypeColor(procurementType)}
            >
              {procurementType}
            </Badge>
          )}
        </div>
      </CardHeader>

      <CardContent className="pb-3 flex-1">
        <p className="text-muted-foreground line-clamp-3 mb-3">
          {rfp.description}
        </p>
        
        <div className="space-y-2">
          {issuer && (
            <div className="flex items-center gap-2 text-sm">
              <Building className="h-4 w-4 text-muted-foreground" />
              <span className="text-muted-foreground">{issuer}</span>
            </div>
          )}
          
          <div className="flex items-center gap-2 text-sm">
            <Calendar className="h-4 w-4 text-muted-foreground" />
            <span className="text-muted-foreground">
              Posted: {format(new Date(rfp.posted_date))}
            </span>
          </div>
          
          {rfp.closing_date && (
            <div className="flex items-center gap-2 text-sm">
              <Calendar className="h-4 w-4 text-destructive" />
              <span className="text-destructive">
                Closes: {format(new Date(rfp.closing_date))}
              </span>
            </div>
          )}
          
          {contractValue && (
            <div className="flex items-center gap-2 text-sm">
              <DollarSign className="h-4 w-4 text-green-600" />
              <span className="text-green-600 font-medium">
                {formatCurrency(Number(contractValue))}
              </span>
            </div>
          )}
        </div>
      </CardContent>

      <CardFooter className="pt-3 border-t flex-col gap-2 mt-auto">
        {/* Primary action buttons */}
        <div className="flex gap-2 w-full">
          <Button
            variant="outline"
            size="sm"
            onClick={() => onViewDetails(rfp)}
            className="flex-1"
          >
            View Details
          </Button>
          
          <Button 
            variant="outline" 
            size="sm"
            onClick={() => window.open(rfp.url, '_blank')}
            className="flex-1 flex items-center justify-center gap-1"
          >
            <ExternalLink className="h-3 w-3" />
            Source
          </Button>
        </div>

        {/* Secondary action button */}
        <Button
          variant="ghost"
          size="sm"
          onClick={() => onIgnore(rfp.id)}
          className="w-full text-muted-foreground hover:text-foreground"
        >
          {isIgnored ? (
            <>
              <Eye className="h-4 w-4 mr-1" />
              Restore
            </>
          ) : (
            <>
              <EyeOff className="h-4 w-4 mr-1" />
              Ignore
            </>
          )}
        </Button>
      </CardFooter>
    </Card>
  );
}